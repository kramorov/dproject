# pages/media_library_editor.py
"""Управление медиабиблиотекой"""
import streamlit as st

# Инициализация сессии
if 'edit_media_id' not in st.session_state:
    st.session_state.edit_media_id = None

from media_library.models import MediaLibraryItem, MediaCategory, MediaTag


def get_items(category_id=None, search=None):
    """Получить элементы с фильтрацией"""
    qs = MediaLibraryItem.objects.select_related('category', 'created_by', 'content_type')
    if category_id:
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(title__icontains=search)
    return qs.order_by('-created_at')


st.set_page_config(page_title="Медиабиблиотека", layout="wide")
st.title("🖼️ Медиабиблиотека")

# ==================== БОКОВАЯ ПАНЕЛЬ ====================
with st.sidebar:
    st.header("🔍 Фильтры")
    categories = MediaCategory.objects.filter(is_active=True)
    cat_options = [{"id": None, "name": "Все категории"}] + [
        {"id": c.id, "name": f"{c.icon} {c.name}"} for c in categories
    ]
    selected_cat = st.selectbox(
        "Категория",
        options=[c["id"] for c in cat_options],
        format_func=lambda x: next(c["name"] for c in cat_options if c["id"] == x)
    )

    search = st.text_input("Поиск по названию")

    st.divider()
    st.header("📤 Загрузить")
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Файл", type=None)
        title = st.text_input("Название")
        description = st.text_area("Описание", height=80)
        category = st.selectbox(
            "Категория",
            options=[c.id for c in categories],
            format_func=lambda x: next((f"{c.icon} {c.name}" for c in categories if c.id == x), "")
        )
        is_public = st.checkbox("Публичный", value=True)
        if st.form_submit_button("Загрузить"):
            if uploaded_file and title.strip():
                item = MediaLibraryItem(
                    title=title.strip(),
                    description=description.strip(),
                    category_id=category,
                    is_public=is_public,
                    media_file=uploaded_file,
                    created_by=st.session_state.get('user')
                )
                item.save()
                st.success(f"Загружено: {item.title}")
                st.rerun()
            else:
                st.error("Название и файл обязательны")

# ==================== ОСНОВНАЯ ОБЛАСТЬ ====================
items = get_items(category_id=selected_cat, search=search)

st.markdown(f"### 📋 Элементы ({items.count()})")

col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
with col1:
    st.caption("Название")
with col2:
    st.caption("Категория")
with col3:
    st.caption("Публичный")
with col4:
    st.caption("Действия")

st.divider()

for item in items[:50]:  # ограничим вывод
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

    with col1:
        if item.media_file:
            ext = item.media_file.name.split('.')[-1].lower() if '.' in item.media_file.name else ''
            icon_map = {'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
                        'pdf': '📕', 'doc': '📝', 'docx': '📝', 'xls': '📊', 'xlsx': '📊',
                        'dwg': '📐', 'dxf': '📐', 'step': '🔧', 'stp': '🔧'}
            icon = icon_map.get(ext, '📎')
        else:
            icon = '📎'
        st.write(f"{icon} **{item.title}**")
        if item.description:
            st.caption(item.description[:80])

    with col2:
        st.write(f"{item.category.icon} {item.category.name}")

    with col3:
        st.write("✅" if item.is_public else "🔒")

    with col4:
        if st.button("✏️", key=f"edit_{item.id}"):
            st.session_state.edit_media_id = item.id
            st.rerun()

# ==================== РЕДАКТИРОВАНИЕ ЭЛЕМЕНТА ====================
if st.session_state.get('edit_media_id'):
    item = MediaLibraryItem.objects.filter(id=st.session_state.edit_media_id).first()
    if item:
        st.divider()
        st.markdown("### ✏️ Редактирование")
        with st.form("edit_form"):
            new_title = st.text_input("Название", value=item.title)
            new_desc = st.text_area("Описание", value=item.description or '', height=100)
            new_cat = st.selectbox(
                "Категория",
                options=[c.id for c in categories],
                index=[c.id for c in categories].index(item.category_id) if item.category_id in [c.id for c in categories] else 0,
                format_func=lambda x: next((f"{c.icon} {c.name}" for c in categories if c.id == x), "")
            )
            new_public = st.checkbox("Публичный", value=item.is_public)

            # GFK — привязка к объекту
            st.markdown("---")
            st.markdown("**🔗 Привязка к объекту**")
            if item.content_object:
                st.info(f"Привязано: {item.content_type} #{item.object_id} — {item.content_object}")
                clear_gfk = st.checkbox("Отвязать")
            else:
                st.caption("Не привязано ни к какому объекту")

            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("💾 Сохранить")
            with col2:
                cancel_btn = st.form_submit_button("↩️ Отмена")

            if save_btn:
                item.title = new_title.strip()
                item.description = new_desc.strip()
                item.category_id = new_cat
                item.is_public = new_public
                if item.content_object and clear_gfk:
                    item.content_type = None
                    item.object_id = None
                item.save()
                st.success("Сохранено")
                st.session_state.edit_media_id = None
                st.rerun()

            if cancel_btn:
                st.session_state.edit_media_id = None
                st.rerun()