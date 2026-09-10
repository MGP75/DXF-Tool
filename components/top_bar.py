"""Main-area header row: file name, Data/Visualization tabs, export button."""
from __future__ import annotations

import streamlit as st

import dxf_engine as engine
from components.css import CssMarker
from components.selection import Selection
from i18n import t


def render(L: str, css: CssMarker, selection: Selection) -> str:
    """Renders the row and returns the active page ("data" or "viz")."""
    top_l, top_r = st.columns([3, 1.4])
    with top_l:
        name_col, tab1_col, tab2_col = st.columns([2, 1, 1.6])
        with name_col:
            st.markdown(
                f"<div style='font-size:16px;font-weight:600;padding-top:6px'>{selection.active_name}</div>",
                unsafe_allow_html=True,
            )
        with tab1_col:
            if st.button(t(L, "tab_data"), key="tab_data_btn", use_container_width=True):
                st.session_state.page = "data"
                st.rerun()
        with tab2_col:
            if selection.analysis is not None:
                if st.button(t(L, "tab_viz"), key="tab_viz_btn", use_container_width=True):
                    st.session_state.page = "viz"
                    st.rerun()
    with top_r:
        if selection.analysis is not None:
            chip_cache = st.session_state.setdefault("chip_cache", {})
            if selection.sel not in chip_cache:
                chip_cache[selection.sel] = engine.export_with_chips(
                    st.session_state.files[selection.sel]["bytes"], selection.analysis,
                )
            chip_bytes = chip_cache[selection.sel]
            st.download_button(
                t(L, "export_btn"), data=chip_bytes,
                file_name=selection.active_name.rsplit(".", 1)[0] + "_chips.dxf",
                mime="application/dxf", use_container_width=True, key="export_btn",
            )
            css.mark("export_btn", "primary")

    page = st.session_state.page if selection.analysis is not None else "data"
    css.mark("tab_data_btn", "tab_active" if page == "data" else "tab_inactive")
    if selection.analysis is not None:
        css.mark("tab_viz_btn", "tab_active" if page == "viz" else "tab_inactive")
    return page
