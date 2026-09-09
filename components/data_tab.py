"""Data tab: material-saved headline, usable surface/mass and the measures table."""
from __future__ import annotations

from typing import Any

import streamlit as st

from i18n import t


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _fmt_mm2(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " mm²"


def render(L: str, stats: dict[str, Any]) -> None:
    st.markdown(f"<div class='dxf-eyebrow'>{t(L,'measures_header')}</div>", unsafe_allow_html=True)
    saved_str = f"{stats['saved_pct']:.2f}".replace(".", ",")
    st.markdown(
        f"<div class='stat-label'>{t(L,'saved')}</div><div class='stat-big'>{saved_str} %</div>",
        unsafe_allow_html=True,
    )

    usable_m2 = stats["usable_mm2"] / 1_000_000
    m1, m2 = st.columns(2)
    with m1:
        usable_str = f"{usable_m2:.2f}".replace(".", ",")
        st.markdown(
            f"<div class='stat-label'>{t(L,'usable_surface')}</div><div class='stat-value'>{usable_str} m²</div>",
            unsafe_allow_html=True,
        )
    with m2:
        mass_str = f"{usable_m2 * st.session_state.areal_mass:.2f}".replace(".", ",")
        st.markdown(
            f"<div class='stat-label'>{t(L,'estimated_mass')}</div><div class='stat-value'>{mass_str} g</div>",
            unsafe_allow_html=True,
        )

    st.session_state.areal_mass = st.number_input(
        t(L, "areal_mass"), min_value=0.0, value=float(st.session_state.areal_mass), step=1.0,
    )

    rows = [
        (t(L, "plies"), _fmt_int(stats["plies"])),
        (t(L, "tested"), _fmt_int(stats["patches_tested"])),
        (t(L, "usable_patches"), _fmt_int(stats["patches_usable"])),
        (t(L, "usable_surface_mm"), _fmt_mm2(stats["usable_mm2"])),
        (t(L, "waste_surface_mm"), _fmt_mm2(stats["waste_mm2"])),
    ]
    rows_html = "".join(f"<div class='row-line'><span class='k'>{k}</span><span class='v'>{v}</span></div>" for k, v in rows)
    st.markdown(f"<div style='border-top:1px solid var(--line);padding-top:4px'>{rows_html}</div>", unsafe_allow_html=True)
