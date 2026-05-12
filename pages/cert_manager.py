# pages/cert_manager.py
"""Управление сертификатами"""
import streamlit as st
from cert_doc.models import CertData, CertVariety, CertRelation
from media_library.models import MediaLibraryItem, MediaCategory
from django.contrib.contenttypes.models import ContentType

# Сессия
if 'edit_cert_id' not in st.session_state:
    st.session_state.edit_cert_id = None
if 'selected_cert_id' not in st.session_state:
    st.session_state.selected_cert_id = None
if 'edit_mode_new' not in st.session_state:
    st.session_state.edit_mode_new = False

st.set_page_config(page_title="Сертификаты", layout="wide")
st.title("📜 Сертификаты")

# ==================== СПРАВОЧНИКИ ДЛЯ ПРИВЯЗКИ ====================
@st.cache_data(ttl=60)
def get_linkable_models(equipment_type_id=None):
    """Модели, к которым можно привязать сертификат. Фильтруются по типу оборудования."""
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
        # Фильтр по equipment_type: если у ModelLine есть поле equipment_type
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


# ==================== БОКОВАЯ ПАНЕЛЬ — ФОРМА ====================
with st.sidebar:
    st.header("📝 Сертификат")

    varieties = list(CertVariety.objects.filter(is_active=True))
    brands = []  # from producers
    try:
        from producers.models import Brands
        brands = list(Brands.objects.filter(is_active=True).order_by('name'))
    except:
        pass

    if st.session_state.edit_mode_new:
        cert = None
        mode = "new"
        st.subheader("➕ Новый сертификат")
    elif st.session_state.edit_cert_id:
        cert = CertData.objects.filter(id=st.session_state.edit_cert_id).first()
        mode = "edit"
        st.subheader("✏️ Редактирование")
    else:
        cert = None
        mode = None

    with st.form("cert_form"):
        name = st.text_input("Название *", value=cert.name if cert else '')
        code = st.text_input("Код", value=cert.code or '' if cert else '')
        description = st.text_area("Описание (серии, бренды)", value=cert.description or '' if cert else '', height=80)
        issued_by = st.text_input("Кем выдан", value=cert.issued_by or '' if cert else '')
        cert_variety = st.selectbox(
            "Тип сертификата",
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

        from core.models import EquipmentType
        etypes = list(EquipmentType.objects.filter(is_active=True).order_by('level', 'sorting_order', 'name'))
        equipment_type_id = st.selectbox(
            "Тип оборудования",
            options=[e.id for e in etypes],
            format_func=lambda x: next((e.name for e in etypes if e.id == x), ''),
            index=next((i for i, e in enumerate(etypes) if cert and e.id == cert.equipment_type_id), 0) if cert and cert.equipment_type_id else 0
        )

        col1, col2 = st.columns(2)
        with col1:
            valid_from = st.date_input("Действует с", value=cert.valid_from if cert else None)
        with col2:
            valid_until = st.date_input("Действует до", value=cert.valid_until if cert else None)

        # Файл сертификата (из медиабиблиотеки или загрузка)
        media_items = MediaLibraryItem.objects.filter(
            category__code='CERTIFICATE', is_active=True
        ).order_by('-created_at')[:100] if cert else []

        media_options = [{'id': None, 'name': '— Без файла —'}] + [
            {'id': m.id, 'name': m.title} for m in media_items
        ]
        current_media = cert.media_item_id if cert else None

        # Если current_media не в списке — добавим
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

        col1, col2 = st.columns(2)
        with col1:
            saved = st.form_submit_button("💾 Сохранить")
        with col2:
            if st.form_submit_button("↩️ Отмена"):
                st.session_state.edit_cert_id = None
                st.session_state.edit_mode_new = False
                st.rerun()

        if saved and name.strip():
            if mode == "new":
                cert = CertData(
                    name=name.strip(),
                    code=code.strip() or None,
                    description=description.strip(),
                    cert_variety_id=cert_variety,
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
            else:
                cert.name = name.strip()
                cert.code = code.strip() or None
                cert.description = description.strip()
                cert.cert_variety_id = cert_variety
                cert.issued_by = issued_by.strip()
                cert.brand_id = brand_id or None
                cert.equipment_type_id = equipment_type_id or None
                cert.valid_from = valid_from
                cert.valid_until = valid_until
                cert.public_url = public_url.strip() or None
                cert.media_item_id = selected_media
                cert.save()
                st.success(f"Обновлён: {cert.name}")

            st.session_state.edit_cert_id = cert.id
            st.session_state.edit_mode_new = False
            st.session_state.selected_cert_id = cert.id
            st.rerun()

    if not st.session_state.edit_cert_id and not st.session_state.edit_mode_new:
        if st.button("➕ Новый сертификат"):
            st.session_state.edit_mode_new = True
            st.rerun()

# ==================== СПИСОК СЕРТИФИКАТОВ ====================
st.markdown("### 📋 Список сертификатов")

certs = CertData.objects.select_related('cert_variety', 'brand', 'media_item').order_by('-valid_until')

for cert in certs[:30]:
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col1:
        st.write(f"📜 **{cert.name}**")
        if cert.description:
            st.caption(cert.description[:100])
    with col2:
        st.write(f"{cert.cert_variety.name if cert.cert_variety else '—'}")
    with col3:
        if cert.valid_until:
            expired = cert.valid_until < __import__('datetime').date.today()
            st.write(f"{'❌' if expired else '✅'} до {cert.valid_until}")
        else:
            st.write('—')
    with col4:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✏️", key=f"editc_{cert.id}"):
                st.session_state.edit_cert_id = cert.id
                st.rerun()
        with c2:
            if st.button("🔗", key=f"links_{cert.id}"):
                st.session_state.selected_cert_id = cert.id
                st.rerun()

# ==================== УПРАВЛЕНИЕ СВЯЗЯМИ ====================
if st.session_state.selected_cert_id:
    cert = CertData.objects.filter(id=st.session_state.selected_cert_id).first()
    if cert:
        st.divider()
        st.markdown(f"### 🔗 Связи сертификата: **{cert.name}**")

        # Существующие связи
        links = CertRelation.objects.filter(cert_data=cert).select_related('content_type')
        if links:
            for link in links:
                col1, col2, col3 = st.columns([5, 1, 1])
                obj = link.content_object
                with col1:
                    ct_name = link.content_type.model_class().__name__ if link.content_type else '—'
                    st.write(f"**{ct_name}**: {obj}")
                with col2:
                    if st.button("❌", key=f"dellink_{link.id}"):
                        link.delete()
                        st.rerun()
        else:
            st.caption("Нет связей. Добавьте серии/модели ниже.")

        # Добавить новую связь
        st.markdown("**➕ Добавить связь:**")
        linkable = get_linkable_models(cert.equipment_type_id)
        # Группируем по типу модели
        model_types = sorted(set(m['model_name'] for m in linkable))
        selected_model_type = st.selectbox("Тип объекта", model_types)
        filtered = [m for m in linkable if m['model_name'] == selected_model_type]

        if filtered:
            selected_obj = st.selectbox(
                "Объект",
                options=range(len(filtered)),
                format_func=lambda i: filtered[i]['name']
            )
            if st.button("🔗 Привязать"):
                obj = filtered[selected_obj]
                ct = ContentType.objects.get(id=obj['ct_id'])
                CertRelation.objects.get_or_create(
                    cert_data=cert,
                    content_type=ct,
                    object_id=obj['obj_id'],
                )
                st.rerun()
