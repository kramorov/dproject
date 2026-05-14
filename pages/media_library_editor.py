# pages/media_library_editor.py
"""Медиабиблиотека — каталог с фильтрацией через SmartCatalogMixin"""
import streamlit as st
from media_library.models import MediaLibraryItem, MediaCategory

st.set_page_config(page_title="Медиабиблиотека", layout="wide")
st.title("🖼️ Медиабиблиотека")

# ==================== СЕССИЯ ====================
if 'edit_media_id' not in st.session_state:
    st.session_state.edit_media_id = None


# ==================== ФИЛЬТРЫ (SmartCatalogMixin) ====================
filter_options = MediaLibraryItem.get_filter_options()

st.markdown("### 🔍 Фильтры")
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_text = st.text_input("Поиск", placeholder="Название, описание, ключевые слова...")

with col2:
    selected_category = None
    if filter_options.get('category_id'):
        selected_category = st.selectbox(
            "Категория",
            [{'id': None, 'name': 'Все'}] + filter_options['category_id'],
            format_func=lambda x: x['name']
        )

with col3:
    selected_equipment_type = None
    if filter_options.get('equipment_type_id'):
        selected_equipment_type = st.selectbox(
            "Тип оборудования",
            [{'id': None, 'name': 'Все'}] + filter_options['equipment_type_id'],
            format_func=lambda x: x['name']
        )

with col4:
    keyword_text = st.text_input("Ключевое слово", placeholder="насос, DN50...")


# ==================== ПАРАМЕТРЫ → filter_by_params ====================
params = {'limit': 100}

if search_text:
    params['search'] = search_text

if selected_category and selected_category.get('id'):
    params['category_id'] = selected_category['id']

if selected_equipment_type and selected_equipment_type.get('id'):
    params['equipment_type_id'] = selected_equipment_type['id']

if keyword_text:
    params['keyword'] = keyword_text

result = MediaLibraryItem.filter_by_params(params)

st.write(f"**Найдено:** {result['total']} | **Показано:** {len(result['data'])}")


# ==================== БОКОВАЯ ПАНЕЛЬ — ЗАГРУЗКА ====================
with st.sidebar:
    st.header("📤 Загрузить")
    categories = MediaCategory.objects.filter(is_active=True)

    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Файл", type=None)
        title = st.text_input("Название")
        description = st.text_area("Описание", height=60)
        keywords = st.text_input("Ключевые слова", placeholder="через запятую")
        category = st.selectbox(
            "Категория",
            options=[c.id for c in categories],
            format_func=lambda x: next(
                (f"{c.icon} {c.name}" for c in categories if c.id == x), ""
            )
        )
        is_public = st.checkbox("Публичный", value=True)
        if st.form_submit_button("Загрузить"):
            if uploaded_file and title.strip():
                item = MediaLibraryItem(
                    title=title.strip(),
                    description=description.strip(),
                    keywords=keywords.strip(),
                    category_id=category,
                    is_public=is_public,
                    media_file=uploaded_file,
                )
                item.save()
                st.success(f"Загружено: {item.title}")
                st.rerun()
            else:
                st.error("Название и файл обязательны")


# ==================== РЕЗУЛЬТАТЫ ====================
st.markdown("### 📋 Результаты")

if not result['data']:
    st.info("Элементы не найдены. Измените фильтры или загрузите новый.")
else:
    for item in result['data']:
        ext = item.get('file_name', '').split('.')[-1].lower() if item.get('file_name') else ''
        icon_map = {
            'pdf': '📕', 'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'dwg': '📐', 'dxf': '📐',
        }
        icon = icon_map.get(ext, '📎')

        col1, col2, col3, col4 = st.columns([4, 2, 1, 1])

        with col1:
            st.write(f"{icon} **{item['title']}**")
            if item.get('description'):
                st.caption(item['description'][:100])
            if item.get('keywords'):
                st.caption(f"🏷️ {item['keywords'][:80]}")

        with col2:
            category = item.get('category')
            if category:
                st.write(f"{category.get('icon', '📁')} {category['name']}")
            else:
                st.write('—')
            etype = item.get('equipment_type')
            if etype:
                st.caption(f"🔧 {etype['name']}")

        with col3:
            st.write("✅" if item.get('is_public') else "🔒")

        with col4:
            if st.button("✏️", key=f"edit_{item['id']}"):
                st.session_state.edit_media_id = item['id']
                st.rerun()


# ==================== РЕДАКТИРОВАНИЕ ====================
if st.session_state.get('edit_media_id'):
    item = MediaLibraryItem.objects.filter(
        id=st.session_state.edit_media_id
    ).first()

    if item:
        st.divider()
        st.markdown(f"### ✏️ Редактирование: **{item.title}**")

        categories = MediaCategory.objects.filter(is_active=True)

        with st.form("edit_form"):
            new_title = st.text_input("Название", value=item.title)
            new_desc = st.text_area("Описание", value=item.description or '', height=80)
            new_keywords = st.text_input(
                "Ключевые слова", value=item.keywords or '',
                placeholder="через запятую"
            )
            new_cat = st.selectbox(
                "Категория",
                options=[c.id for c in categories],
                index=[c.id for c in categories].index(item.category_id)
                if item.category_id in [c.id for c in categories] else 0,
                format_func=lambda x: next(
                    (f"{c.icon} {c.name}" for c in categories if c.id == x), ""
                )
            )
            new_public = st.checkbox("Публичный", value=item.is_public)
            new_active = st.checkbox("Активен", value=item.is_active)

            # equipment_type — отдельно
            from core.models import EquipmentType
            etypes = list(EquipmentType.objects.filter(is_active=True).order_by('level', 'name'))
            etype_options = [None] + [e.id for e in etypes]
            etype_index = 0
            if item.equipment_type_id:
                for i, eid in enumerate(etype_options):
                    if eid == item.equipment_type_id:
                        etype_index = i
                        break
            new_equipment_type = st.selectbox(
                "Тип оборудования",
                options=etype_options,
                format_func=lambda x: next(
                    (e.name for e in etypes if e.id == x), "— Не указан —"
                ),
                index=etype_index
            )

            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("💾 Сохранить")
            with col2:
                cancel_btn = st.form_submit_button("↩️ Отмена")

            if save_btn:
                item.title = new_title.strip()
                item.description = new_desc.strip()
                item.keywords = new_keywords.strip()
                item.category_id = new_cat
                item.is_public = new_public
                item.is_active = new_active
                item.equipment_type_id = new_equipment_type or None
                item.save()
                st.success("Сохранено")
                st.session_state.edit_media_id = None
                st.rerun()

            if cancel_btn:
                st.session_state.edit_media_id = None
                st.rerun()
