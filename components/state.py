"""Session state defaults."""
from __future__ import annotations

import streamlit as st

DEFAULTS = {
    "theme": "light",
    "lang": "fr",
    "page": "viz",
    "view": "binary",
    "areal_mass": 204.0,
    "files": {},       # file_id -> {name, size, bytes, status, analysis, error}
    "order": [],        # upload order of file_ids
    "selected": None,   # file_id or "__total__"
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
