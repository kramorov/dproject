# pages/request_edit.py
import streamlit as st
from datetime import datetime
import uuid

from clients.models import Company
from db_init import init_django

init_django()

from client_requests.models import ClientRequest , ClientRequestStatus , ClientRequestItem , RequestItemType
from project_customers.utils import get_streamlit_customer_user

st.set_page_config(
    page_title="Запрос клиента" ,
    page_icon="📋" ,
    layout="wide"
)


def get_request(request_id) :
    """Получить запрос по ID"""
    try :
        return ClientRequest.objects.get(id=request_id)
    except ClientRequest.DoesNotExist :
        return None


def get_request_items(request_id) :
    """Получить все позиции запроса"""
    try :
        return ClientRequestItem.objects.filter(
            request_parent_id=request_id ,
            is_current=True ,
            status='active'
        ).order_by('item_no')
    except :
        return []


def save_request(request , form_data , is_new=False) :
    """Сохранить изменения запроса"""
    request.name = form_data.get('name')
    request.client_request_number = form_data.get('client_request_number')
    request.end_customer = form_data.get('end_customer')
    request.request_status_id = form_data.get('status_id')
    request.request_from_client_company_id = form_data.get('company_id')
    request.request_responsible_person_id = form_data.get('responsible_person_id')
    request.request_text = form_data.get('request_text')
    request.request_date = form_data.get('request_date')
    request.required_by_date = form_data.get('required_by_date')
    request.internal_notes = form_data.get('internal_notes')
    request.orders_1c = form_data.get('orders_1c')
    request.bitrix_deal_id = form_data.get('bitrix_deal_id')

    if is_new :
        # Для новых запросов устанавливаем владельца
        current_user , current_company = get_streamlit_customer_user()
        request.project_customer_user_request_owner = current_user
        request.project_customer_request_owner = current_company
        # Устанавливаем статус "Новый" для новых запросов
        if not request.request_status_id :
            new_status = ClientRequestStatus.get_default_status()
            if new_status :
                request.request_status_id = new_status.id

    request.save()

    # Сохраняем позиции запроса
    if 'request_items' in form_data and form_data['request_items'] :
        save_request_items(request , form_data['request_items'] , is_new)
        # Устанавливаем флаг для перезагрузки из БД
        st.session_state.force_reload_from_db = True

    return request


def save_request_items(request , items_data , is_new=False) :
    """Сохранить позиции запроса"""
    import logging
    logger = logging.getLogger(__name__)

    logger.error(f"=== save_request_items CALLED ===")
    logger.error(f"Request ID: {request.id}")
    logger.error(f"is_new: {is_new}")
    logger.error(f"items_data: {items_data}")
    logger.error(f"Количество позиций: {len(items_data) if items_data else 0}")

    if not items_data :
        logger.error("Нет данных для сохранения")
        return

    # Получаем текущие позиции
    existing_items = {item.item_no : item for item in
                      ClientRequestItem.objects.filter(
                          request_parent=request ,
                          is_current=True ,
                          status='active'
                      )}

    logger.error(f"Существующие позиции в БД: {len(existing_items)}")

    # Обрабатываем позиции из формы
    for item_data in items_data :
        item_no = item_data.get('item_no')
        logger.error(f"Обработка позиции {item_no}: {item_data}")

        version = 1

        if item_no in existing_items :
            # Обновляем существующую позицию
            logger.error(f"Обновление существующей позиции {item_no}")
            existing_item = existing_items[item_no]
            existing_item.item_type_id = item_data.get('item_type_id')
            existing_item.request_line_ol = item_data.get('request_line_ol' , '')
            existing_item.request_line_text = item_data.get('request_line_text' , '')
            existing_item.save()
            del existing_items[item_no]
        else :
            # Создаем новую позицию
            logger.error(f"Создание новой позиции {item_no}")
            try :
                new_item = ClientRequestItem.objects.create(
                    request_parent=request ,
                    item_no=item_no ,
                    version=version ,
                    is_current=True ,
                    item_type_id=item_data.get('item_type_id') ,
                    request_line_ol=item_data.get('request_line_ol' , '') ,
                    request_line_text=item_data.get('request_line_text' , '') ,
                    status='active'
                )
                logger.error(f"Создана позиция ID: {new_item.id}")
            except Exception as e :
                logger.error(f"Ошибка при создании: {e}")

    # Удаляем позиции, которых больше нет в форме
    for item_no , item in existing_items.items() :
        logger.error(f"Удаление позиции {item_no}")
        item.is_current = False
        item.status = 'deleted'
        item.save()

    logger.error("=== save_request_items FINISHED ===")


def render_request_item_card(item , idx) :
    """Рендер компактной карточки позиции запроса"""

    # Получаем тип подбора для отображения
    item_type_name = ""
    if item.get('item_type_id') :
        try :
            item_type = RequestItemType.objects.get(id=item['item_type_id'])
            item_type_name = item_type.name
        except RequestItemType.DoesNotExist :
            item_type_name = "Тип не найден"
        except Exception as e :
            item_type_name = f"Ошибка: {str(e)}"

    # Компактная карточка с использованием нативных компонентов Streamlit
    with st.container(border=True) :
        col1 , col2 = st.columns([4 , 1])

        with col1 :
            # Основная информация в caption (маленький шрифт)
            ol_value = item.get('request_line_ol' , '') or "не указан"
            text_preview = item.get('request_line_text' , '')
            if text_preview and len(text_preview) > 80 :
                text_preview = text_preview[:80] + "..."
            elif not text_preview :
                text_preview = "не указан"

            st.caption(
                f"📦 **Поз.{item['item_no']}** | 📄 ОЛ: {ol_value} | 🏷️ {item_type_name if item_type_name else 'тип не выбран'}")
            st.caption(f"📝 {text_preview}")

        with col2 :
            # Кнопки в одной строке
            col_btn1 , col_btn2 = st.columns(2)
            with col_btn1 :
                if st.button("✏️" , key=f"edit_{idx}" , help="Редактировать") :
                    st.session_state.edit_item_data = item.copy()
                    st.session_state.edit_item_index = idx
                    st.session_state.is_new_item = False
                    st.switch_page("pages/request_item_edit.py")
            with col_btn2 :
                if st.button("🗑️" , key=f"del_{idx}" , help="Удалить") :
                    st.session_state.delete_item_idx = idx
                    st.rerun()


def render_request_items_form(request , is_edit=False) :
    """Рендер формы для позиций запроса"""

    st.markdown("### 📦 Позиции запроса")

    # Обработка удаления
    if 'delete_item_idx' in st.session_state :
        idx = st.session_state.delete_item_idx
        if 'request_items' in st.session_state :
            st.session_state.request_items.pop(idx)
            # Перенумеровываем позиции
            for new_idx , item in enumerate(st.session_state.request_items , start=1) :
                item['item_no'] = new_idx
        del st.session_state.delete_item_idx
        st.rerun()

    # Обработка результата редактирования (возврат из request_item_edit.py)
    if 'edit_item_saved' in st.session_state and st.session_state.edit_item_saved :
        result = st.session_state.edit_item_result
        if result :
            # Инициализируем request_items если нужно
            if 'request_items' not in st.session_state :
                st.session_state.request_items = []

            idx = result.get('index')
            if idx >= 0 and idx < len(st.session_state.request_items) :
                # Обновляем существующую позицию
                st.session_state.request_items[idx] = {
                    'item_no' : result['item_no'] ,
                    'item_type_id' : result['item_type_id'] ,
                    'request_line_ol' : result['request_line_ol'] ,
                    'request_line_text' : result['request_line_text']
                }
            else :
                # Добавляем новую позицию
                st.session_state.request_items.append({
                    'item_no' : result['item_no'] ,
                    'item_type_id' : result['item_type_id'] ,
                    'request_line_ol' : result['request_line_ol'] ,
                    'request_line_text' : result['request_line_text']
                })

            # Сортируем и перенумеровываем позиции
            st.session_state.request_items.sort(key=lambda x : x['item_no'])
            for new_idx , item in enumerate(st.session_state.request_items , start=1) :
                item['item_no'] = new_idx

        # Очищаем флаги
        st.session_state.edit_item_saved = False
        if 'edit_item_result' in st.session_state :
            del st.session_state.edit_item_result
        if 'edit_item_data' in st.session_state :
            del st.session_state.edit_item_data
        if 'edit_item_index' in st.session_state :
            del st.session_state.edit_item_index
        if 'is_new_item' in st.session_state :
            del st.session_state.is_new_item
        st.rerun()

    # Загружаем позиции из БД ТОЛЬКО если request_items пустой или это новый запрос
    # НЕ перезаписываем session_state если там уже есть данные (после добавления/редактирования)
    if request and request.id :
        # Проверяем, нужно ли загружать из БД
        should_load_from_db = False

        if 'request_items' not in st.session_state :
            should_load_from_db = True
        elif not st.session_state.request_items :
            should_load_from_db = True
        elif st.session_state.get('force_reload_from_db' , False) :
            should_load_from_db = True
            st.session_state.force_reload_from_db = False

        if should_load_from_db :
            items_from_db = get_request_items(request.id)
            st.session_state.request_items = [
                {
                    'item_no' : item.item_no ,
                    'item_type_id' : item.item_type_id ,
                    'request_line_ol' : item.request_line_ol or '' ,
                    'request_line_text' : item.request_line_text or ''
                }
                for item in items_from_db
            ]
    else :
        # Для нового запроса инициализируем пустой список
        if 'request_items' not in st.session_state :
            st.session_state.request_items = []

    # Кнопка добавления новой позиции
    col1 , col2 , col3 = st.columns([1 , 1 , 4])
    with col1 :
        if st.button("➕ Добавить позицию" , use_container_width=True , type="primary") :
            st.session_state.edit_item_data = {
                'item_no' : max([item['item_no'] for item in st.session_state.request_items] , default=0) + 1 ,
                'item_type_id' : None ,
                'request_line_ol' : '' ,
                'request_line_text' : ''
            }
            st.session_state.edit_item_index = -1
            st.session_state.is_new_item = True
            st.switch_page("pages/request_item_edit.py")

    # Отображаем карточки позиций
    if st.session_state.request_items :
        for idx , item in enumerate(st.session_state.request_items) :
            render_request_item_card(item , idx)
        st.caption(f"📊 Всего позиций: {len(st.session_state.request_items)}")
    else :
        st.info("💡 Нет добавленных позиций. Нажмите 'Добавить позицию' чтобы создать первую позицию.")

    return st.session_state.request_items


def render_request_form(request , is_edit=False , is_new=False) :
    """Рендер формы запроса"""

    # Получаем текущего пользователя для фильтрации
    current_user , _ = get_streamlit_customer_user()

    st.markdown("### 📋 Данные запроса")

    # Основная информация
    col1 , col2 = st.columns(2)

    with col1 :
        # Номер заявки
        if is_edit and not is_new :
            st.text_input("Номер заявки" , value=request.code or "" , disabled=True)
        else :
            code = st.text_input("Номер заявки" , value=request.code or "" ,
                                 placeholder="Будет сгенерирован автоматически")

        # Название заявки
        name = st.text_input("Название заявки *" , value=request.name or "")

        # Номер заявки клиента
        client_request_number = st.text_input("Номер заявки клиента" , value=request.client_request_number or "")

        # Конечный заказчик
        end_customer = st.text_input("Конечный заказчик" , value=request.end_customer or "")

    with col2 :
        # Дата запроса
        request_date = st.date_input(
            "Дата запроса *" ,
            value=request.request_date or datetime.now().date()
        )

        # Требуемая дата
        required_by_date = st.date_input(
            "Требуемая дата" ,
            value=request.required_by_date if request.required_by_date else datetime.now().date() ,
            help="Желаемая дата выполнения"
        )

        # Статус (для новых запросов - "Новый")
        statuses = ClientRequestStatus.get_choices()
        status_options = [(s.id , s.name) for s in statuses]

        # Для нового запроса выбираем статус "Новый"
        if is_new :
            default_status = ClientRequestStatus.get_default_status()
            current_status_id = default_status.id if default_status else (
                status_options[0][0] if status_options else None)
        else :
            current_status_id = request.request_status_id if request.request_status_id else (
                status_options[0][0] if status_options else None
            )

        status_id = st.selectbox(
            "Статус" ,
            options=status_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , s in enumerate(status_options) if s[0] == current_status_id) , 0)
        )[0]

    # Компании и ответственные
    st.markdown("### 🏢 Клиент")
    col1 , col2 = st.columns(2)

    with col1 :
        # Получаем компании для выпадающего списка
        company_choices = Company.get_choices(owner_user=current_user)
        company_options = [(0 , "— Выберите —")] + [(c['id'] , c['name']) for c in company_choices]
        current_company_id = request.request_from_client_company_id if request.request_from_client_company_id else 0
        company_id = st.selectbox(
            "Компания клиента" ,
            options=company_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , c in enumerate(company_options) if c[0] == current_company_id) , 0) ,
            key="company_select"
        )[0]

    with col2 :
        # Ответственное лицо
        st.markdown("### 👤 Ответственное лицо")

        person_choices = Company.get_person_choices(
            company_id=company_id if company_id != 0 else None ,
            owner_user=current_user
        )
        is_disabled = (company_id == 0)

        # Если есть только один сотрудник, автоматически выбираем его
        if len(person_choices) == 1 and not is_disabled :
            default_person_id = person_choices[0]['id']
        else :
            default_person_id = request.request_responsible_person_id if request.request_responsible_person_id else 0

        person_options = [(0 , "— Не выбрано —")] + [(p['id'] , p['name']) for p in person_choices]

        responsible_person_id = st.selectbox(
            "Ответственное лицо" ,
            options=person_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , p in enumerate(person_options) if p[0] == default_person_id) , 0) ,
            disabled=is_disabled
        )[0]

    # Текст запроса
    st.markdown("### 📝 Текст запроса")
    request_text = st.text_area(
        "Текст запроса" ,
        value=request.request_text or "" ,
        height=150
    )

    # Позиции запроса
    request_items = render_request_items_form(request if not is_new else None , is_edit)

    # Внутренние заметки
    internal_notes = st.text_area(
        "Внутренние заметки" ,
        value=request.internal_notes or "" ,
        height=100 ,
        help="Заметки для внутреннего использования"
    )

    # Интеграции
    st.markdown("### 🔌 Интеграции")
    col1 , col2 = st.columns(2)

    with col1 :
        orders_1c = st.text_input("Заказы в 1С" , value=request.orders_1c or "" , placeholder="Номера через запятую")

    with col2 :
        bitrix_deal_id = st.text_input("ID сделки в Битрикс24" , value=request.bitrix_deal_id or "")

    # Кнопки
    col1 , col2 , col3 = st.columns([1 , 1 , 1])

    with col1 :
        if st.button("💾 Сохранить" , use_container_width=True) :
            form_data = {
                'name' : name ,
                'code' : code if is_new or not is_edit else request.code ,
                'client_request_number' : client_request_number ,
                'end_customer' : end_customer ,
                'status_id' : status_id if status_id != 0 else None ,
                'company_id' : company_id if company_id != 0 else None ,
                'responsible_person_id' : responsible_person_id if responsible_person_id != 0 else None ,
                'request_text' : request_text ,
                'request_date' : request_date ,
                'required_by_date' : required_by_date if required_by_date else None ,
                'internal_notes' : internal_notes ,
                'orders_1c' : orders_1c ,
                'bitrix_deal_id' : bitrix_deal_id ,
                'request_items' : request_items
            }
            return form_data , True

    with col2 :
        if st.button("🔙 Назад к списку" , use_container_width=True) :
            # Очищаем session state при выходе
            if 'request_items' in st.session_state :
                del st.session_state.request_items
            st.switch_page("pages/request_list.py")

    with col3 :
        if is_edit and not is_new and st.button("🗑 Удалить" , use_container_width=True) :
            return None , 'delete'

    return None , False


def main() :
    # Определяем режим
    is_new = st.session_state.get('create_new_request' , False)
    request_id = st.session_state.get('view_request_id') or st.session_state.get('edit_request_id')
    is_edit = 'edit_request_id' in st.session_state

    # Создание нового запроса
    if is_new :
        st.title("➕ Новый запрос клиента")

        # Создаем пустой объект запроса
        request = ClientRequest()
        request.request_date = datetime.now().date()

        # Рендер формы
        form_data , saved = render_request_form(request , is_edit=False , is_new=True)

        if saved and form_data :
            request = save_request(request , form_data , is_new=True)
            st.success(f"✅ Запрос {request.code} успешно создан!")
            # Очищаем session_state
            if 'create_new_request' in st.session_state :
                del st.session_state.create_new_request
            if 'request_items' in st.session_state :
                del st.session_state.request_items
            st.switch_page("pages/request_list.py")

        if st.button("🔙 Отмена") :
            if 'create_new_request' in st.session_state :
                del st.session_state.create_new_request
            if 'request_items' in st.session_state :
                del st.session_state.request_items
            st.switch_page("pages/request_list.py")
        return

    # Просмотр/редактирование существующего
    if not request_id :
        st.error("❌ Запрос не найден")
        if st.button("🔙 Вернуться к списку") :
            st.switch_page("pages/request_list.py")
        return

    # Получаем запрос
    request = get_request(request_id)

    if not request :
        st.error("❌ Запрос не найден")
        if st.button("🔙 Вернуться к списку") :
            st.switch_page("pages/request_list.py")
        return

    # Заголовок
    if is_edit :
        st.title(f"✏️ Редактирование запроса {request.code or ''}")
    else :
        st.title(f"📋 Просмотр запроса {request.code or ''}")

    # Рендер формы
    form_data , saved = render_request_form(request , is_edit=is_edit , is_new=False)

    if saved and form_data :
        request = save_request(request , form_data)
        st.success(f"✅ Запрос {request.code} успешно сохранен!")
        # Очищаем session_state для позиций
        if 'request_items' in st.session_state :
            del st.session_state.request_items
        st.rerun()

    if saved == 'delete' :
        request_id = request.id
        request.delete()
        st.success(f"✅ Запрос удален!")
        # Очищаем session_state
        if 'view_request_id' in st.session_state :
            del st.session_state.view_request_id
        if 'edit_request_id' in st.session_state :
            del st.session_state.edit_request_id
        if 'request_items' in st.session_state :
            del st.session_state.request_items
        st.switch_page("pages/request_list.py")


if __name__ == "__main__" :
    main()