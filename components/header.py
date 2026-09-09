"""Top header bar: app title, language switch, theme toggle, reset, user."""
from __future__ import annotations

import streamlit as st

from components.css import CssMarker
from i18n import t


def _toggle_theme() -> None:
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"


def _do_reset() -> None:
    st.session_state.files = {}
    st.session_state.order = []
    st.session_state.selected = None
    st.session_state.page = "viz"
    st.session_state.chip_cache = {}
    # Swaps in a fresh file_uploader widget so previously dropped files don't
    # get silently re-ingested on the next run (the widget keeps its own state).
    st.session_state.uploader_version = st.session_state.get("uploader_version", 0) + 1


def _set_lang(code: str) -> None:
    st.session_state.lang = code


def render(L: str, css: CssMarker) -> None:
    h_left, h_right = st.columns([3, 5])
    with h_left:
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:14px;padding-top:6px'>"
            f"<span class='dxf-title'>{t(L,'app_name')}</span>"
            f"<span class='mono muted' style='font-size:13px'>{t(L,'version')}</span></div>",
            unsafe_allow_html=True,
        )
    with h_right:
        c_fr, c_en, c_ar, c_theme, c_reset, c_user = st.columns([1, 1, 1, 1.8, 2, 2.6])
        for code, col, label in [("fr", c_fr, "FR"), ("en", c_en, "EN"), ("ar", c_ar, "AR")]:
            with col:
                st.button(label, key=f"lang_{code}", on_click=_set_lang, args=(code,), use_container_width=True)
            if L == code:
                css.mark(f"lang_{code}", "pill_active")
        with c_theme:
            st.button(
                t(L, "theme_to_dark") if st.session_state.theme == "light" else t(L, "theme_to_light"),
                key="theme_toggle", on_click=_toggle_theme, use_container_width=True,
            )
        with c_reset:
            st.button(t(L, "reset"), key="reset_btn", on_click=_do_reset, use_container_width=True)
            css.mark("reset_btn", "ghost")
        with c_user:
            st.markdown(
                "<div class='muted' style='text-align:right;padding-top:8px;font-size:14px'>maxence.gendrot@safrangroup.com</div>",
                unsafe_allow_html=True,
            )
    st.markdown("<hr style='margin:8px 0 16px'>", unsafe_allow_html=True)
