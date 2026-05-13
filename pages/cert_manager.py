# pages/cert_manager.py
"""Управление сертификатами"""
import streamlit as st
from cert_doc.models import CertData, CertVariety
from media_library.models import MediaLibraryItem, MediaCategory
from django.db.models import Q

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
def get_models_with_cert_docs():
    """Возвращает список классов моделей, у которых есть поле cert_docs (M2M к CertData)."""
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from pa_controls.models.lsb_model_line import LimitSwitchModelLine

    candidates = [
        PneumaticActuatorModelLine,
        LimitSwitchModelLine,
    ]
    return [cls for cls in candidates if hasattr(cls, 'cert_docs')]


def get_linkable_objects(cert):
    """
    Возвращает объекты model_line, к которым можно привязать сертификат.
    Фильтрация: model_line.equipment_type входит в cert.equipment_types.
    Исключаются уже привязанные.
    """
    available = []
    cert_type_ids = list(cert.equipment_types.values_list('id', flat=True))

    for cls in get_models_with_cert_docs():
        qs = cls.objects.filter(is_active=True)
        if cert_type_ids and hasattr(cls, 'equipment_type'):
            qs = qs.filter(equipment_type_id__in=cert_type_ids)
        # Исключаем уже привязанные
        already_linked_ids = cls.objects.filter(cert_docs=cert).values_list('id', flat=True)
        qs = qs.exclude(id__in=already_linked_ids)
        for obj in qs.order_by('name')[:500]:
            available.append({
                'model_name': cls.__name__,
                'obj': obj,
                'display': str(obj),
            })
    return available


# ==================== БОКОВАЯ ПАНЕЛЬ — ФОРМА ====================
with st.sidebar:
    st.header("📝 Сертификат")

    varieties = list(CertVariety.objects.filter(is_active=True))
    brands = []
    try:
        from producers.models import Brands
        brands = list(Brands.objects.filter(is_active=True).order_by('name'))
    except Exception:
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
        description = st.text_area(
            "Описание (серии, бренды)",
            value=cert.description or '' if cert else '',
            height=80
        )
        issued_by = st.text_input("Кем выдан", value=cert.issued_by or '' if cert else '')
        cert_variety = st.selectbox(
            "Тип сертификата",
            options=[v.id for v in varieties],
            format_func=lambda x: next((v.name for v in varieties if v.id == x), ''),
            index=next(
                (i for i, v in enumerate(varieties) if cert and v.id == cert.cert_variety_id), 0
            ) if cert else 0
        )
        brand_id = st.selectbox(
            "Бренд",
            options=[b.id for b in brands],
            format_func=lambda x: next((b.name for b in brands if b.id == x), ''),
            index=next(
                (i for i, b in enumerate(brands) if cert and b.id == cert.brand_id), 0
            ) if cert and cert.brand_id else 0
        )

        # === Типы оборудования (M2M, multiselect) ===
        from core.models import EquipmentType
        etypes = list(EquipmentType.objects.filter(is_active=True).order_by(
            'level', 'sorting_order', 'name'
        ))
        # Дефолт: выбранные типы для существующего сертификата
        default_et_ids = (
            list(cert.equipment_types.values_list('id', flat=True))
            if cert else []
        )
        selected_et_ids = st.multiselect(
            "Типы оборудования",
            options=[e.id for e in etypes],
            format_func=lambda x: next((e.name for e in etypes if e.id == x), ''),
            default=default_et_ids
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

        if current_media and current_media not in [m['id'] for m in media_options]:
            existing = MediaLibraryItem.objects.filter(id=current_media).first()
            if existing:
                media_options.append({'id': existing.id, 'name': existing.title})

        selected_media = st.selectbox(
            "Файл PDF",
            options=[m['id'] for m in media_options],
            format_func=lambda x: next(
                (m['name'] for m in media_options if m['id'] == x), ''
            ),
            index=next(
                (i for i, m in enumerate(media_options) if m['id'] == current_media), 0
            )
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
                    valid_from=valid_from,
                    valid_until=valid_until,
                    public_url=public_url.strip() or None,
                    media_item_id=selected_media,
                )
                cert.save()
                cert.equipment_types.set(selected_et_ids)
                st.success(f"Создан: {cert.name}")
            else:
                cert.name = name.strip()
                cert.code = code.strip() or None
                cert.description = description.strip()
                cert.cert_variety_id = cert_variety
                cert.issued_by = issued_by.strip()
                cert.brand_id = brand_id or None
                cert.valid_from = valid_from
                cert.valid_until = valid_until
                cert.public_url = public_url.strip() or None
                cert.media_item_id = selected_media
                cert.save()
                cert.equipment_types.set(selected_et_ids)
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

certs = CertData.objects.select_related(
    'cert_variety', 'brand', 'media_item'
).prefetch_related('equipment_types').order_by('-valid_until')

for cert in certs[:30]:
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col1:
        st.write(f"📜 **{cert.name}**")
        if cert.description:
            st.caption(cert.description[:100])
        et_names = ', '.join(e.name for e in cert.equipment_types.all())
        if et_names:
            st.caption(f"Типы: {et_names}")
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


# ==================== УПРАВЛЕНИЕ СВЯЗЯМИ (M2M cert_docs) ====================
if st.session_state.selected_cert_id:
    cert = CertData.objects.filter(id=st.session_state.selected_cert_id).first()
    if cert:
        st.divider()
        st.markdown(f"### 🔗 Связи сертификата: **{cert.name}**")

        # --- Существующие связи ---
        linked_objects = []
        for cls in get_models_with_cert_docs():
            for obj in cls.objects.filter(cert_docs=cert).order_by('name'):
                linked_objects.append({
                    'model_name': cls.__name__,
                    'obj': obj,
                    'display': str(obj),
                })

        if linked_objects:
            for item in linked_objects:
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.write(f"**{item['model_name']}**: {item['display']}")
                with col2:
                    if st.button("❌", key=f"dellink_{item['obj'].id}_{item['model_name']}"):
                        item['obj'].cert_docs.remove(cert)
                        st.rerun()
        else:
            st.caption("Нет связей. Добавьте серии/модели ниже.")

        # --- Добавить новую связь ---
        st.markdown("**➕ Добавить связь:**")
        available = get_linkable_objects(cert)

        if available:
            # Группируем по типу модели
            model_types = sorted(set(m['model_name'] for m in available))
            selected_model_type = st.selectbox("Тип объекта", model_types)
            filtered = [m for m in available if m['model_name'] == selected_model_type]

            if filtered:
                selected_idx = st.selectbox(
                    "Объект",
                    options=range(len(filtered)),
                    format_func=lambda i: filtered[i]['display']
                )
                if st.button("🔗 Привязать"):
                    obj = filtered[selected_idx]['obj']
                    obj.cert_docs.add(cert)
                    st.rerun()
        else:
            st.caption("Нет доступных объектов для привязки. Проверьте, что у сертификата указаны типы оборудования, а у серий — совпадающий equipment_type.")
