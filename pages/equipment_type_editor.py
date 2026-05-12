# pages/equipment_type_editor.py
"""Редактор иерархического справочника EquipmentType"""
import streamlit as st
from core.models import EquipmentType

st.set_page_config(page_title="Редактор типов оборудования", layout="wide")
st.title("📂 Редактор типов оборудования")

# ==================== ИНИЦИАЛИЗАЦИЯ СЕССИИ ====================
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None  # None | 'add' | 'edit'
if 'parent_candidate' not in st.session_state:
    st.session_state.parent_candidate = None
if 'expanded_nodes' not in st.session_state:
    st.session_state.expanded_nodes = set()


def get_tree():
    """Получить всё дерево EquipmentType"""
    return EquipmentType.objects.select_related('parent').all()


def get_roots():
    """Корневые узлы (без родителя)"""
    return EquipmentType.objects.filter(parent__isnull=True).order_by('sorting_order', 'name')


def get_children(parent):
    """Дочерние узлы для parent"""
    return parent.children.order_by('sorting_order', 'name')


def render_node(node, depth=0):
    """Отрисовать узел дерева рекурсивно"""
    indent = " " * depth
    has_children = node.children.exists()
    node_key = f"node_{node.id}"

    # Раскрытие/сворачивание
    is_expanded = node.id in st.session_state.expanded_nodes
    expand_icon = "▼" if is_expanded else "▶"
    if has_children:
        toggle_label = f"{expand_icon} {indent}{node.icon or '📁'} {node.name}"
    else:
        toggle_label = f"{indent}{'  ' if depth>0 else ''}{node.icon or '📄'} {node.name}"

    col1, col2, col3, col4 = st.columns([6, 1, 1, 1])

    with col1:
        if has_children:
            if st.button(toggle_label, key=f"toggle_{node.id}", use_container_width=True):
                if is_expanded:
                    st.session_state.expanded_nodes.discard(node.id)
                else:
                    st.session_state.expanded_nodes.add(node.id)
                st.rerun()
        else:
            st.markdown(f"{indent} {node.icon or '📄'} **{node.name}**")
        st.caption(f"{indent}  код: {node.code or '—'} | уровень: {node.level} | {'✅' if node.is_active else '❌'}")

    with col2:
        if st.button("✏️", key=f"edit_{node.id}", help="Редактировать"):
            st.session_state.selected_id = node.id
            st.session_state.edit_mode = 'edit'
            st.rerun()

    with col3:
        if st.button("➕", key=f"add_child_{node.id}", help="Добавить дочерний"):
            st.session_state.parent_candidate = node.id
            st.session_state.edit_mode = 'add'
            st.rerun()

    with col4:
        # Не даём удалять узлы с детьми
        if not has_children:
            if st.button("🗑️", key=f"delete_{node.id}", help="Удалить"):
                node.delete()
                st.session_state.expanded_nodes.discard(node.id)
                st.rerun()
        else:
            st.caption(f"📂{node.children.count()}")

    if has_children and is_expanded:
        for child in get_children(node):
            render_node(child, depth + 1)


# ==================== БОКОВАЯ ПАНЕЛЬ — ФОРМА РЕДАКТИРОВАНИЯ ====================
with st.sidebar:
    st.header("🔧 Редактор")

    if st.session_state.edit_mode == 'add':
        st.subheader("➕ Добавление")
        parent_id = st.session_state.parent_candidate
        parent = EquipmentType.objects.filter(id=parent_id).first() if parent_id else None
        parent_name = parent.name if parent else "Корень"
        st.info(f"Родитель: **{parent_name}**")

    elif st.session_state.edit_mode == 'edit' and st.session_state.selected_id:
        st.subheader("✏️ Редактирование")
        obj = EquipmentType.objects.filter(id=st.session_state.selected_id).first()
        if obj:
            st.info(f"Редактирование: **{obj.name}** (id={obj.id})")

    # Поля формы
    if st.session_state.edit_mode in ('add', 'edit'):
        # Предзаполняем если редактирование
        if st.session_state.edit_mode == 'edit' and obj:
            default_name = obj.name or ''
            default_code = obj.code or ''
            default_desc = obj.description or ''
            default_icon = obj.icon or ''
            default_active = obj.is_active
            default_order = obj.sorting_order
            default_parent = obj.parent_id
        else:
            default_name = ''
            default_code = ''
            default_desc = ''
            default_icon = ''
            default_active = True
            default_order = 0
            default_parent = st.session_state.parent_candidate if st.session_state.edit_mode == 'add' else None

        with st.form("equipment_type_form"):
            name = st.text_input("Название *", value=default_name, key="form_name")
            code = st.text_input("Код", value=default_code, key="form_code")
            description = st.text_area("Описание", value=default_desc, key="form_desc", height=100)
            icon = st.text_input("Иконка (emoji)", value=default_icon, key="form_icon",
                                 placeholder="Например: 🏭 или 🔧")
            sorting_order = st.number_input("Порядок сортировки", value=default_order, step=1)
            is_active = st.checkbox("Активно", value=default_active)

            # Выбор родителя
            all_types = [(None, "— Корень —")] + [
                (t.id, f"{'  '*t.level}{t.icon or ''} {t.name}")
                for t in EquipmentType.objects.filter(is_active=True).order_by('level', 'sorting_order', 'name')
            ]
            # Нельзя выбирать себя или потомка как родителя
            if st.session_state.edit_mode == 'edit' and obj:
                descendants = set(obj.get_descendants_ids())
                descendants.add(obj.id)
                allowed_types = [(tid, tname) for tid, tname in all_types if tid not in descendants]
            else:
                allowed_types = all_types

            parent_choices = [tname for _, tname in allowed_types]
            parent_ids = [tid for tid, _ in allowed_types]
            default_idx = parent_ids.index(default_parent) if default_parent in parent_ids else 0
            selected_parent_name = st.selectbox(
                "Родительский тип",
                options=parent_choices,
                index=default_idx,
                key="form_parent"
            )
            selected_parent_id = parent_ids[parent_choices.index(selected_parent_name)]

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Сохранить", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("↩️ Отмена", use_container_width=True)

            if submit and name.strip():
                try:
                    if st.session_state.edit_mode == 'add':
                        new_obj = EquipmentType(
                            name=name.strip(),
                            code=code.strip() or None,
                            description=description.strip(),
                            icon=icon.strip(),
                            sorting_order=sorting_order,
                            is_active=is_active,
                            parent_id=selected_parent_id
                        )
                        new_obj.save()
                        st.success(f"✅ Создано: {new_obj.name}")
                        st.session_state.edit_mode = None
                        st.session_state.parent_candidate = None
                        st.rerun()
                    elif st.session_state.edit_mode == 'edit':
                        obj.name = name.strip()
                        obj.code = code.strip() or None
                        obj.description = description.strip()
                        obj.icon = icon.strip()
                        obj.sorting_order = sorting_order
                        obj.is_active = is_active
                        obj.parent_id = selected_parent_id
                        obj.save()
                        st.success(f"✅ Обновлено: {obj.name}")
                        st.session_state.edit_mode = None
                        st.session_state.selected_id = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {e}")

            if cancel:
                st.session_state.edit_mode = None
                st.session_state.selected_id = None
                st.session_state.parent_candidate = None
                st.rerun()

    else:
        # Режим просмотра — кнопки действий
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Корневой узел", use_container_width=True):
                st.session_state.edit_mode = 'add'
                st.session_state.parent_candidate = None
                st.rerun()
        with col2:
            if st.button("🔄 Обновить", use_container_width=True):
                st.session_state.expanded_nodes = set()
                st.rerun()

        # Статистика
        total = EquipmentType.objects.count()
        active = EquipmentType.objects.filter(is_active=True).count()
        st.metric("Всего узлов", total)
        st.metric("Активных", active)

# ==================== ОСНОВНАЯ ОБЛАСТЬ — ДЕРЕВО ====================
st.markdown("### 🌳 Иерархия типов оборудования")

if st.button("📂 Развернуть всё", use_container_width=True):
    all_ids = set(EquipmentType.objects.values_list('id', flat=True))
    st.session_state.expanded_nodes = all_ids
    st.rerun()

st.divider()

# Отрисовка дерева
roots = get_roots()
if roots:
    for root in roots:
        render_node(root, 0)
else:
    st.info("Нет узлов. Добавьте первый узел через боковую панель.")
