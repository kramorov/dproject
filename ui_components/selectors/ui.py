#ui_components/selectors/ui.py
import streamlit as st
from typing import List, Dict, Any, Optional, Callable


def render_selectbox(
        label: str,
        options: Dict[int, str],
        key: str,
        default_id: int = 0,
        disabled: bool = False,
        on_change: Optional[Callable] = None
) -> int:
    """
    Чистый UI компонент селектора.
    Ничего не знает о бизнес-логике, только отображает себя.
    """
    selected_id = st.selectbox(
        label=label,
        options=list(options.keys()),
        format_func=lambda x: options.get(x, "Выберите"),
        key=key,
        disabled=disabled
    )

    if on_change and selected_id != default_id:
        on_change(selected_id)

    return selected_id