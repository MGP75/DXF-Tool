"""Deferred "active state" CSS for widgets rendered elsewhere on the page."""
from __future__ import annotations

import streamlit as st

import styles


class CssMarker:
    """Collects per-widget active-state CSS rules while the page is built
    and flushes them as one <style> block at the end.

    Whether a button/card should render as "active" often depends on state
    that's only known once later widgets have been drawn (e.g. the current
    tab or view), so rules are gathered here and emitted together via
    flush() — a <style> tag applies globally regardless of where it sits in
    the DOM, so this is safe.
    """

    def __init__(self) -> None:
        self._blocks: list[str] = []

    def mark(self, key: str, variant: str, target: str = "button") -> None:
        self._blocks.append(styles.key_style(key, variant, target))

    def flush(self) -> None:
        st.markdown("\n".join(self._blocks), unsafe_allow_html=True)
