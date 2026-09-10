"""Turning uploaded DXF files into analyzed session-state entries."""
from __future__ import annotations

import hashlib

import streamlit as st

import dxf_engine as engine
from i18n import t


def make_fid(name: str, size: int) -> str:
    # A plain slug (not the raw name) so it can double as a Streamlit
    # widget/container key: Streamlit sanitizes keys into CSS classes,
    # and only a key that is already "safe" is guaranteed to match the
    # `.st-key-<key>` selectors used for the active-state styling.
    digest = hashlib.md5(f"{name}:{size}".encode()).hexdigest()[:12]
    return f"f{digest}"


def analyze_new_file(L: str, name: str, data: bytes) -> tuple[str, engine.DxfAnalysis | None, str | None]:
    status_box = st.empty()
    bar = st.progress(0.0)
    step_labels = {
        "step_read": t(L, "step_read"), "step_extract": t(L, "step_extract"),
        "step_patch": t(L, "step_patch"), "step_measure": t(L, "step_measure"),
    }

    def on_progress(frac: float, step_key: str) -> None:
        frac = min(frac, 1.0)
        bar.progress(frac)
        status_box.markdown(
            f"<span class='mono muted'>{step_labels[step_key]} · {int(frac * 100)} %</span>",
            unsafe_allow_html=True,
        )

    status, analysis, error = "analyzed", None, None
    try:
        analysis = engine.analyze_bytes(name, data, progress=on_progress)
    except Exception as exc:  # malformed DXF, unsupported entities, etc.
        status, error = "error", str(exc)
    bar.empty()
    status_box.empty()
    return status, analysis, error


def ingest_uploads(uploaded, L: str) -> bool:
    """Analyze any newly-uploaded files and store the results in session
    state. Returns True if new files were added (caller should st.rerun())."""
    new_files = [f for f in uploaded if make_fid(f.name, f.size) not in st.session_state.files]
    for f in new_files:
        fid = make_fid(f.name, f.size)
        data = f.getvalue()
        st.session_state.files[fid] = {
            "name": f.name, "size": f.size, "bytes": data,
            "status": "pending", "analysis": None, "error": None,
        }
        st.session_state.order.append(fid)
        status, analysis, error = analyze_new_file(L, f.name, data)
        st.session_state.files[fid].update(status=status, analysis=analysis, error=error)
        if st.session_state.selected is None:
            st.session_state.selected = fid
    return bool(new_files)
