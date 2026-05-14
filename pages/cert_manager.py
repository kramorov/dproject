# pages/cert_manager.py
"""Управление сертификатами — каталог с фильтрацией и редактированием"""
import streamlit as st
from cert_doc.models import CertData, CertVariety, CertRelation
from media_library.models import MediaLibraryItem
from django.contrib.contenttypes.models import ContentType

st.set_page_config(page_title="Сертификаты", layout="wide")
st.title("📜 Сертификаты")

# ==================== СЕССИЯ ====================
if 'edit_cert_id' not in st.session_state:
    st.session_state.edit_cert_id = None
if 'edit_mode_new' not in st.session_state:
    st.session_state.edit_mode_new = False
if 'selected_cert_id' not in st.session_state:
    st.session_state.selected_cert_id = None


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
@st.cache_data(ttl=60)
def get_linkable_models(equipment_type_id=None):
    """Модели, к которым можно привязать сертификат."""
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from electric_actuators.models import ElectricActuatorModelLine
    from pneumatic_fittings.models import PneumaticFittingModelLine
    from solenoid_valves.models import DirectionalValveModelLine
    from gearbox.models import GearBoxModelLine
    from pa_controls.models.lsb_model_line import LimitSwitchModelLine

    all_cls = [
        PneumaticActuatorModelLine,
        ElectricActuatorModelLine,
        PneumaticFittingModelLine,
        DirectionalValveModelLine,
        GearBoxModelLine,
        LimitSwitchModelLine,
    ]

    models = []
    for cls in all_cls:
        ct = ContentType.objects.get_for_model(cls)
        qs = cls.objects.filter(is_active=True)
        if equipment_type_id and hasattr(cls, 'equipment_type'):
            qs = qs.filter(equipment_type_id=equipment_type_id)
        for obj in qs.order_by('name')[:500]:
            models.append({
                'ct_id': ct.id,
                'obj_id': obj.id,
                'name': str(obj),
                'model_name': cls.__name__,
            })
    return models


# ==================== ФИЛЬТРЫ (верхняя часть) ====================
filter_options = CertData.get_filter_options()

st.markdown("### 🔍 Фильтры")
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_text = st.text_input("Поиск", placeholder="Код, название, кем выдан...")

with col2:
    selected_variety = None
    if filter_options.get('cert_variety_id'):
        selected_variety = st.selectbox(
            "Тип сертификата",
            [{'id': None, 'name': 'Все'}] + filter_options['cert_variety_id'],
            format_func=lambda x: x['name']
        )

with col3:
    selected_brand = None
    if filter_options.get('brand_id'):
        selected_brand = st.selectbox(
            "Бренд",
            [{'id': None, 'name': 'Все'}] + filter_options['brand_id'],
            format_func=lambda x: x['name']
        )

with col4:
    selected_equipment_type = None
    if filter_options.get('equipment_type_id'):
        selected_equipment_type = st.selectbox(
            "Тип оборудования",
            [{'id': None, 'name': 'Все'}] + filter_options['equipment_type_id'],
            format_func=lambda x: x['name']
        )

# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
params = {'limit': 100}

if search_text:
    params['search'] = search_text

if selected_variety and selected_variety.get('id'):
    params['cert_variety_id'] = selected_variety['id']

if selected_brand and selected_brand.get('id'):
    params['brand_id'] = selected_brand['id']

if selected_equipment_type and selected_equipment_type.get('id'):
    params['equipment_type_id'] = selected_equipment_type['id']

# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = CertData.filter_by_params(params)

st.write(f"**Найдено:** {result['total']} | **Показано:** {len(result['data'])}")

# ==================== ФОРМА РЕДАКТИРОВАНИЯ ====================
if st.session_state.edit_mode_new or st.session_state.edit_cert_id:
    st.divider()

    varieties = list(CertVariety.objects.filter(is_active=True))
    try:
        from producers.models import Brands
        brands = list(Brands.objects.filter(is_active=True).order_by('name'))
    except Exception:
        brands = []

    from core.models import EquipmentType
    etypes = list(EquipmentType.objects.filter(is_active=True).order_by('level', 'sorting_order', 'name'))

    if st.session_state.edit_mode_new:
        cert = None
        st.markdown("### ➕ Новый сертификат")
    else:
        cert = CertData.objects.filter(id=st.session_state.edit_cert_id).first()
        st.markdown(f"### ✏️ Редактирование: **{cert.name if cert else '—'}**")

    with st.form("cert_edit_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Название *", value=cert.name if cert else '')
            code = st.text_input("Код", value=cert.code or '' if cert else '')
            issued_by = st.text_input("Кем выдан", value=cert.issued_by or '' if cert else '')

        with col2:
            cert_variety_id = st.selectbox(
                "Тип сертификата *",
                options=[v.id for v in varieties],
                format_func=lambda x: next((v.name for v in varieties if v.id == x), ''),
                index=next((i for i, v in enumerate(varieties) if cert and v.id == cert.cert_variety_id), 0) if cert else 0
            )
            brand_id = st.selectbox(
                "Бренд",
                options=[b.id for b in brands],
                format_func=lambda x: next((b.name for b in brands if b.id == x), ''),
                index=next((i for i, b in enumerate(brands) if cert and b.id == cert.brand_id), 0) if cert and cert.brand_id else 0
            )
            equipment_type_id = st.selectbox(
                "Тип оборудования",
                options=[e.id for e in etypes],
                format_func=lambda x: next((e.name for e in etypes if e.id == x), ''),
                index=next((i for i, e in enumerate(etypes) if cert and e.id == cert.equipment_type_id), 0) if cert and cert.equipment_type_id else 0
            )

        description = st.text_area("Описание", value=cert.description or '' if cert else '', height=80)

        col1, col2 = st.columns(2)
        with col1:
            valid_from = st.date_input("Действует с", value=cert.valid_from if cert else None)
        with col2:
            valid_until = st.date_input("Действует до", value=cert.valid_until if cert else None)

        # Медиафайл
        media_items = MediaLibraryItem.objects.filter(
            category__code='CERTIFICATE', is_active=True
        ).order_by('-created_at')[:100]

        media_options = [{'id': None, 'name': '— Без файла —'}] + [
            {'id': m.id, 'name': m.title} for m in media_items
        ]
        current_media = cert.media_item_id if cert else None

        if current_media and current_media not in [m['id'] for m in media_options]:
            existing = MediaLibraryItem.objects.filter(id=current_media).first()
            if existing:
                media_options.append({'id': existing.id, 'name': existing.title})

        selected_media = st.selectbox(
            "Файл PDF",
            options=[m['id'] for m in media_options],
            format_func=lambda x: next((m['name'] for m in media_options if m['id'] == x), ''),
            index=next((i for i, m in enumerate(media_options) if m['id'] == current_media), 0)
        )

        public_url = st.text_input("URL", value=cert.public_url or '' if cert else '')

        col1, col2, col3 = st.columns(3)
        with col1:
            saved = st.form_submit_button("💾 Сохранить")
        with col2:
            cancelled = st.form_submit_button("↩️ Отмена")

        if saved and name.strip():
            if st.session_state.edit_mode_new:
                cert = CertData(
                    name=name.strip(),
                    code=code.strip() or None,
                    description=description.strip(),
                    cert_variety_id=cert_variety_id,
                    issued_by=issued_by.strip(),
                    brand_id=brand_id or None,
                    equipment_type_id=equipment_type_id or None,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    public_url=public_url.strip() or None,
                    media_item_id=selected_media,
                )
                cert.save()
                st.success(f"Создан: {cert.name}")
                st.session_state.edit_cert_id = cert.id
                st.session_state.edit_mode_new = False
            else:
                cert.name = name.strip()
                cert.code = code.strip() or None
                cert.description = description.strip()
                cert.cert_variety_id = cert_variety_id
                cert.issued_by = issued_by.strip()
                cert.brand_id = brand_id or None
                cert.equipment_type_id = equipment_type_id or None
                cert.valid_from = valid_from
                cert.valid_until = valid_until
                cert.public_url = public_url.strip() or None
                cert.media_item_id = selected_media
                cert.save()
                st.success(f"Обновлён: {cert.name}")

            st.rerun()

        if cancelled:
            st.session_state.edit_cert_id = None
            st.session_state.edit_mode_new = False
            st.rerun()


# ==================== БЛОК УПРАВЛЕНИЯ СВЯЗЯМИ ====================
if st.session_state.edit_cert_id and not st.session_state.edit_mode_new:
    cert_id = st.session_state.edit_cert_id
    edit_cert = CertData.objects.filter(id=cert_id).first()
    if edit_cert:
        st.divider()
        st.markdown(f"### 🔗 Связи сертификата: **{edit_cert.name}**")

        # --- Существующие связи ---
        links = CertRelation.objects.filter(cert_data=edit_cert).select_related('content_type')
        if links.exists():
            for link in links:
                lcol1, lcol2 = st.columns([12, 1])
                with lcol1:
                    ct_name = link.content_type.model_class().__name__ if link.content_type else '—'
                    obj = link.content_object
                    st.write(f"**{ct_name}**: {obj}")
                with lcol2:
                    if st.button("❌", key=f"dellink_{link.id}"):
                        print(f"[CERT_MANAGER] delete link id={link.id}")
                        link.delete()
                        st.success("Связь удалена")
                        st.rerun()
        else:
            st.caption("Нет связей.")

        # --- Добавить новую связь ---
        st.markdown("**➕ Добавить связь:**")

        print(f"[CERT_MANAGER] loading linkable models for equipment_type_id={edit_cert.equipment_type_id}")
        linkable = get_linkable_models(edit_cert.equipment_type_id)
        print(f"[CERT_MANAGER] linkable count={len(linkable)}")

        if not linkable:
            st.warning("Нет доступных объектов для привязки. Проверьте тип оборудования сертификата.")
        else:
            model_types = sorted(set(m['model_name'] for m in linkable))
            selected_model_type = st.selectbox(
                "Тип объекта", model_types,
                key=f"link_model_type_{cert_id}"
            )
            filtered = [m for m in linkable if m['model_name'] == selected_model_type]

            if filtered:
                selected_obj_idx = st.selectbox(
                    "Объект",
                    options=range(len(filtered)),
                    format_func=lambda i: filtered[i]['name'],
                    key=f"link_object_{cert_id}"
                )

                if st.button("🔗 Привязать", key=f"link_btn_{cert_id}"):
                    print(f"[CERT_MANAGER] link button clicked, cert_id={cert_id}")
                    print(f"[CERT_MANAGER] selected_obj_idx={selected_obj_idx}, filtered_len={len(filtered)}")

                    obj_meta = filtered[selected_obj_idx]
                    print(f"[CERT_MANAGER] obj_meta={obj_meta}")

                    try:
                        ct = ContentType.objects.get(id=obj_meta['ct_id'])
                        print(f"[CERT_MANAGER] content_type={ct.app_label}.{ct.model}")
                    except ContentType.DoesNotExist:
                        print(f"[CERT_MANAGER] ERROR: ContentType id={obj_meta['ct_id']} not found!")
                        st.error(f"❌ ContentType id={obj_meta['ct_id']} не найден")
                        st.stop()

                    print(f"[CERT_MANAGER] calling get_or_create: cert_data_id={edit_cert.id}, ct={ct.id}, object_id={obj_meta['obj_id']}")

                    try:
                        relation, created = CertRelation.objects.get_or_create(
                            cert_data=edit_cert,
                            content_type=ct,
                            object_id=obj_meta['obj_id'],
                        )
                        print(f"[CERT_MANAGER] get_or_create result: created={created}, relation_id={relation.id}")
                    except Exception as e:
                        print(f"[CERT_MANAGER] EXCEPTION in get_or_create: {type(e).__name__}: {e}")
                        import traceback
                        traceback.print_exc()
                        st.error(f"❌ Ошибка при создании связи: {type(e).__name__}: {e}")
                        st.stop()

                    if created:
                        st.success(f"✅ Связь добавлена: {obj_meta['name']}")
                        print(f"[CERT_MANAGER] SUCCESS: link created")
                    else:
                        st.warning(f"⚠️ Такая связь уже существует: {obj_meta['name']}")
                        print(f"[CERT_MANAGER] WARNING: link already exists")

                    st.rerun()

        # Кнопка закрыть
        if st.button("✖️ Закрыть связи", key=f"close_links_{cert_id}"):
            st.session_state.edit_cert_id = None
            st.session_state.selected_cert_id = None
            st.rerun()


# ==================== КНОПКА «НОВЫЙ СЕРТИФИКАТ» ====================
if not st.session_state.edit_cert_id and not st.session_state.edit_mode_new:
    if st.button("➕ Новый сертификат"):
        st.session_state.edit_mode_new = True
        st.session_state.selected_cert_id = None
        st.rerun()


# ==================== РЕЗУЛЬТАТЫ ====================
st.markdown("### 📋 Результаты")

if not result['data']:
    st.info("Сертификаты не найдены. Измените фильтры или создайте новый.")
else:
    for item in result['data']:
        is_selected = (st.session_state.selected_cert_id == item['id'])
        is_expired = False
        if item.get('valid_until'):
            from datetime import date
            is_expired = date.today() > date.fromisoformat(item['valid_until'])

        status_icon = '❌' if is_expired else '✅'
        title = f"{status_icon} {item['name'] or 'Без названия'}"
        if item.get('code'):
            title += f" ({item['code']})"

        with st.expander(title, expanded=is_selected):
            col1, col2, col3 = st.columns(3)

            with col1:
                variety = item.get('cert_variety')
                st.write(f"**Тип:** {variety['name'] if variety else '—'}")
                st.write(f"**Код:** {item.get('code') or '—'}")

                brand = item.get('brand')
                st.write(f"**Бренд:** {brand['name'] if brand else '—'}")

            with col2:
                st.write(f"**Выдан:** {item.get('issued_by') or '—'}")
                valid_from = item.get('valid_from')
                valid_until = item.get('valid_until')
                if valid_from or valid_until:
                    parts = []
                    if valid_from:
                        parts.append(f"с {valid_from}")
                    if valid_until:
                        parts.append(f"до {valid_until}")
                    st.write(f"**Срок:** {' '.join(parts)}")
                else:
                    st.write("**Срок:** не указан")

                etype = item.get('equipment_type')
                st.write(f"**Тип оборудования:** {etype['name'] if etype else '—'}")

            with col3:
                if item.get('has_media'):
                    st.write("📎 **Файл:** прикреплён")
                else:
                    st.write("📎 **Файл:** —")

                if item.get('public_url'):
                    st.write(f"🔗 [Ссылка]({item['public_url']})")
                else:
                    st.write("🔗 **URL:** —")

                st.write(f"**Активен:** {'Да' if item.get('is_active') else 'Нет'}")

            if item.get('description'):
                st.caption(f"📝 {item['description'][:200]}")

            # --- Связи сертификата ---
            cert_links = CertRelation.objects.filter(
                cert_data_id=item['id']
            ).select_related('content_type')[:20]

            if cert_links:
                st.markdown("**🔗 Связи:**")
                for cl in cert_links:
                    ct_name = cl.content_type.model if cl.content_type else '—'
                    obj = cl.content_object
                    obj_name = str(obj) if obj else f"#{cl.object_id}"
                    st.caption(f"• {ct_name}: {obj_name}")
            else:
                st.caption("🔗 Нет связей")

            # Кнопки действий
            col1, col2, col3 = st.columns([1, 1, 9])
            with col1:
                if st.button("✏️", key=f"edit_{item['id']}"):
                    st.session_state.edit_cert_id = item['id']
                    st.session_state.edit_mode_new = False
                    st.session_state.selected_cert_id = None
                    st.rerun()
            with col2:
                if st.button("🔗", key=f"links_{item['id']}"):
                    st.session_state.edit_cert_id = item['id']
                    st.session_state.selected_cert_id = item['id']
                    st.session_state.edit_mode_new = False
                    st.rerun()
