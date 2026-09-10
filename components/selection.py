"""Resolving the currently-selected file (or the "Total" view) into the
data the main area needs to render."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

import dxf_engine as engine
from components.css import CssMarker
from i18n import t


@dataclass
class Selection:
    sel: str
    analysis: engine.DxfAnalysis | None
    stats: dict[str, Any]
    active_name: str


def analyzed_files() -> list[engine.DxfAnalysis]:
    return [
        st.session_state.files[fid]["analysis"]
        for fid in st.session_state.order
        if st.session_state.files[fid]["status"] == "analyzed"
    ]


def resolve_selection(L: str, css: CssMarker) -> Selection:
    """Figure out what the main area should show. The empty, error and
    loading states have no further content, so this stops the script (after
    flushing pending CSS) right here for those cases."""
    sel = st.session_state.selected

    if sel is None:
        st.markdown(
            f"<div style='padding:64px 16px'>"
            f"<div style='font-size:22px;font-weight:500;margin-bottom:12px'>{t(L,'empty_title')}</div>"
            f"<p class='muted' style='max-width:520px;font-size:15px;line-height:1.5'>{t(L,'empty_body')}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        css.flush()
        st.stop()

    if sel == "__total__":
        analyzed = analyzed_files()
        return Selection(
            sel=sel, analysis=None,
            stats=engine.combine(analyzed),
            active_name=t(L, "total_files", n=len(analyzed)),
        )

    entry = st.session_state.files.get(sel)
    if entry is None:
        st.session_state.selected = None
        st.rerun()

    active_name = entry["name"]
    if entry["status"] == "error":
        st.markdown(
            f"<div style='padding:64px 16px'>"
            f"<div style='font-size:22px;font-weight:500;margin-bottom:12px'>{active_name}</div>"
            f"<p style='color:#B3452F;font-size:15px'>{t(L,'parse_error', err=entry['error'])}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        css.flush()
        st.stop()

    if entry["status"] != "analyzed":
        st.info(t(L, "loading_title"))
        css.flush()
        st.stop()

    analysis = entry["analysis"]
    stats = {
        "plies": analysis.plies, "patches_tested": analysis.patches_tested,
        "patches_usable": analysis.patches_usable, "usable_mm2": analysis.usable_mm2,
        "waste_mm2": analysis.waste_mm2, "envelope_mm2": analysis.envelope_mm2,
        "saved_pct": analysis.saved_pct,
    }
    return Selection(sel=sel, analysis=analysis, stats=stats, active_name=active_name)
