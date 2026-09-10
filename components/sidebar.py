"""Sidebar: file list, file selection and the DXF uploader."""
from __future__ import annotations

import streamlit as st

from components import file_pipeline
from components.css import CssMarker
from components.selection import analyzed_files
from i18n import t


def _select_file(fid: str) -> None:
    st.session_state.selected = fid


def _render_file_card(fid: str, L: str, css: CssMarker) -> None:
    entry = st.session_state.files[fid]
    size_kb = entry["size"] / 1024
    size_label = f"{size_kb/1024:.1f} Mo" if size_kb > 1024 else f"{size_kb:.1f} Ko"
    status_key = {"analyzed": "analyzed", "error": "error"}.get(entry["status"], "in_progress")
    status = f"{size_label} · {t(L, status_key)}"

    with st.container(border=True, key=f"file_{fid}"):
        st.markdown(
            f"<span class='file-name'>{entry['name']}</span><span class='file-status'>{status}</span>",
            unsafe_allow_html=True,
        )
        st.button(t(L, "select_file"), key=f"pick_{fid}", on_click=_select_file, args=(fid,), use_container_width=True)
    if st.session_state.selected == fid:
        css.mark(f"file_{fid}", "card_active", target="self")


def _render_total_card(L: str, css: CssMarker, n: int) -> None:
    with st.container(border=True, key="file_total"):
        st.markdown(
            f"<span class='file-name'>{t(L,'total_files', n=n)}</span>"
            f"<span class='file-status'>{t(L,'cumulative')}</span>",
            unsafe_allow_html=True,
        )
        st.button(t(L, "select_file"), key="pick_total", on_click=_select_file, args=("__total__",), use_container_width=True)
    if st.session_state.selected == "__total__":
        css.mark("file_total", "card_active", target="self")


def render(L: str, css: CssMarker) -> None:
    with st.sidebar:
        st.markdown(f"<div class='dxf-eyebrow'>{t(L,'files_header')}</div>", unsafe_allow_html=True)

        for fid in st.session_state.order:
            _render_file_card(fid, L, css)

        analyzed = analyzed_files()
        if len(analyzed) >= 2:
            _render_total_card(L, css, len(analyzed))

        uploader_version = st.session_state.get("uploader_version", 0)
        uploaded = st.file_uploader(
            t(L, "drop_file"), type=["dxf"], accept_multiple_files=True, key=f"uploader_{uploader_version}",
        )
        st.caption(t(L, "browse"))

        if uploaded and file_pipeline.ingest_uploads(uploaded, L):
            st.rerun()
