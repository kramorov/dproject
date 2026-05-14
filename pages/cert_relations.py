# pages/cert_relations.py
"""Управление связями сертификатов — отдельная страница"""
import sys
import streamlit as st
from cert_doc.models import CertData, CertRelation
from django.contrib.contenttypes.models import ContentType

st.set_page_config(page_title="Связи сертификатов", layout="wide")
st.title("🔗 Связи сертификатов")

print("[CERT_REL] ===== page loaded =====", flush=True)

# ==================== ВЫБОР СЕРТИФИКАТА ====================
certs = list(CertData.objects.filter(is_active=True).order_by('name'))
if not certs:
    st.warning("Нет активных сертификатов.")
    st.stop()

cert_options = {f"{c.name} (id={c.id})": c.id for c in certs}
selected_label = st.selectbox(
    "Сертификат",
    options=list(cert_options.keys()),
    key="cert_select"
)
cert_id = cert_options[selected_label]
cert = CertData.objects.get(id=cert_id)

print(f"[CERT_REL] selected cert: id={cert.id}, name={cert.name}", flush=True)

# ==================== СУЩЕСТВУЮЩИЕ СВЯЗИ ====================
st.divider()
st.subheader(f"Связи: {cert.name}")

links = CertRelation.objects.filter(cert_data=cert).select_related('content_type')
print(f"[CERT_REL] existing links count={links.count()}", flush=True)

if links.exists():
    for link in links:
        col1, col2, col3 = st.columns([3, 6, 1])
        with col1:
            ct_name = link.content_type.model if link.content_type else '—'
            st.write(f"**{ct_name}**")
        with col2:
            obj = link.content_object
            st.write(str(obj) if obj else f"obj_id={link.object_id}")
        with col3:
            if st.button("❌", key=f"del_{link.id}"):
                print(f"[CERT_REL] deleting link id={link.id}", flush=True)
                link.delete()
                st.success("Удалено")
                st.rerun()
else:
    st.info("Связей пока нет.")

# ==================== ДОБАВИТЬ СВЯЗЬ ====================
st.divider()
st.subheader("➕ Добавить связь")


@st.cache_data(ttl=60)
def load_linkable(cert_equipment_type_id):
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
        if cert_equipment_type_id and hasattr(cls, 'equipment_type'):
            qs = qs.filter(equipment_type_id=cert_equipment_type_id)
        for obj in qs.order_by('name')[:500]:
            models.append({
                'ct_id': ct.id,
                'obj_id': obj.id,
                'name': str(obj),
                'model_name': cls.__name__,
            })
    return models


print(f"[CERT_REL] loading linkable for equipment_type_id={cert.equipment_type_id}", flush=True)
linkable = load_linkable(cert.equipment_type_id)
print(f"[CERT_REL] linkable count={len(linkable)}", flush=True)

if not linkable:
    st.warning("Нет доступных объектов для привязки.")
else:
    model_types = sorted(set(m['model_name'] for m in linkable))

    col1, col2, col3 = st.columns([3, 5, 2])
    with col1:
        selected_type = st.selectbox("Тип", model_types, key="add_type")
    filtered = [m for m in linkable if m['model_name'] == selected_type]

    with col2:
        if filtered:
            selected_idx = st.selectbox(
                "Объект",
                options=range(len(filtered)),
                format_func=lambda i: filtered[i]['name'],
                key="add_object"
            )

    with col3:
        st.markdown("### ")
        if filtered:
            if st.button("🔗 Привязать", key="add_btn", type="primary"):
                print(f"[CERT_REL] >>> BUTTON CLICKED <<<", flush=True)
                print(f"[CERT_REL] cert_id={cert.id}, selected_idx={selected_idx}", flush=True)

                obj_meta = filtered[selected_idx]
                print(f"[CERT_REL] obj_meta={obj_meta}", flush=True)

                try:
                    ct = ContentType.objects.get(id=obj_meta['ct_id'])
                    print(f"[CERT_REL] ct={ct.app_label}.{ct.model}", flush=True)
                except ContentType.DoesNotExist:
                    print(f"[CERT_REL] ERROR: ct not found", flush=True)
                    st.error(f"ContentType id={obj_meta['ct_id']} не найден")
                    st.stop()

                print(f"[CERT_REL] get_or_create: cert={cert.id} ct={ct.id} obj={obj_meta['obj_id']}", flush=True)
                try:
                    relation, created = CertRelation.objects.get_or_create(
                        cert_data=cert,
                        content_type=ct,
                        object_id=obj_meta['obj_id'],
                    )
                    print(f"[CERT_REL] created={created}, relation_id={relation.id}", flush=True)
                except Exception as e:
                    print(f"[CERT_REL] EXCEPTION: {type(e).__name__}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    st.error(f"Ошибка: {type(e).__name__}: {e}")
                    st.stop()

                if created:
                    st.success(f"Добавлено: {obj_meta['name']}")
                    print(f"[CERT_REL] SUCCESS", flush=True)
                else:
                    st.warning(f"Уже существует: {obj_meta['name']}")
                    print(f"[CERT_REL] EXISTS", flush=True)

                st.rerun()
