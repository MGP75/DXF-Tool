"""DXF Tool — Streamlit implementation of the "DXF Tool - Maquette" design.

Upload one or more DXF cutting files; the app parses their closed contours,
runs a patch-grid nesting test against the fabric envelope, and reports the
usable surface, waste and estimated mass. Real analysis via ezdxf + shapely.

This module only wires the page together; each region (header, sidebar,
tabs...) is rendered by a component under components/.
"""
from __future__ import annotations

import streamlit as st

import styles
from components import data_tab, header, sidebar, state, top_bar, viz_tab
from components.css import CssMarker
from components.selection import resolve_selection
from i18n import t

st.set_page_config(page_title="DXF Tool", layout="wide", initial_sidebar_state="expanded")

state.init_state()
L = st.session_state.lang

# Base styling (fonts, colors, hiding Streamlit chrome) is injected right
# away so the page never flashes unstyled while a file is being analyzed.
st.markdown(styles.inject(st.session_state.theme, rtl=(L == "ar")), unsafe_allow_html=True)

css = CssMarker()

header.render(L, css)
sidebar.render(L, css)

# Resolves the selected file/"Total" view; stops the script itself (after
# flushing pending CSS) for the empty, error and loading states.
selection = resolve_selection(L, css)

page = top_bar.render(L, css, selection)
st.markdown("<hr>", unsafe_allow_html=True)

if page == "viz" and selection.analysis is not None:
    viz_tab.render(L, css, selection.analysis)
else:
    data_tab.render(L, selection.stats)

st.markdown(f"<div class='dxf-footer'>{t(L,'footer')}</div>", unsafe_allow_html=True)
css.flush()
