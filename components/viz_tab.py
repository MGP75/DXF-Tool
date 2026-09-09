"""Visualization tab: binary/gradient nesting heatmap."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import dxf_engine as engine
import styles
from components.css import CssMarker
from i18n import t


def _render_view_switch(L: str, css: CssMarker) -> None:
    seg_a, seg_b, _ = st.columns([1, 1.3, 4])
    with seg_a:
        if st.button(t(L, "view_binary"), key="view_binary_btn", use_container_width=True):
            st.session_state.view = "binary"
            st.rerun()
    with seg_b:
        if st.button(t(L, "view_gradient"), key="view_gradient_btn", use_container_width=True):
            st.session_state.view = "gradient"
            st.rerun()
    css.mark("view_binary_btn", "pill_active" if st.session_state.view == "binary" else "tab_inactive")
    css.mark("view_gradient_btn", "pill_active" if st.session_state.view == "gradient" else "tab_inactive")


def _build_figure(L: str, analysis: engine.DxfAnalysis) -> go.Figure:
    tokens = styles.DARK if st.session_state.theme == "dark" else styles.LIGHT
    if st.session_state.view == "binary":
        colorscale = [[0, tokens["dashed"]], [0.999, tokens["dashed"]], [1, tokens["accent"]]]
        showscale = False
    else:
        colorscale = [[0, tokens["dashed"]], [1, tokens["accent"]]]
        showscale = True

    fig = go.Figure(
        data=go.Heatmap(
            z=analysis.grid_z, x=analysis.grid_x, y=analysis.grid_y,
            colorscale=colorscale, showscale=showscale, zmin=0, zmax=1,
            hovertemplate="x: %{x:.0f} mm<br>y: %{y:.0f} mm<extra></extra>",
        )
    )
    minx, miny, maxx, maxy = analysis.bounds
    fig.add_shape(type="rect", x0=minx, y0=miny, x1=maxx, y1=maxy, line=dict(color=tokens["ink"], width=1))
    fig.update_layout(
        paper_bgcolor=tokens["surface"], plot_bgcolor=tokens["hatch-a"],
        font=dict(family="IBM Plex Mono, monospace", color=tokens["muted"], size=12),
        margin=dict(l=10, r=10, t=30, b=10), height=460,
        xaxis=dict(scaleanchor="y", showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        title=dict(
            text=t(L, "canvas_caption",
                   tested=f"{analysis.patches_tested:,}".replace(",", " "),
                   usable=f"{analysis.patches_usable:,}".replace(",", " ")),
            font=dict(size=13),
        ),
    )
    return fig


def _render_legend(L: str) -> None:
    st.markdown(
        f"<div class='legend'>"
        f"<span><span class='swatch' style='background:var(--accent)'></span>{t(L,'legend_usable')}</span>"
        f"<span><span class='swatch' style='background:var(--dashed)'></span>{t(L,'legend_waste')}</span>"
        f"<span><span class='swatch' style='border:1px solid var(--ink);background:transparent'></span>{t(L,'legend_envelope')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render(L: str, css: CssMarker, analysis: engine.DxfAnalysis) -> None:
    _render_view_switch(L, css)
    fig = _build_figure(L, analysis)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    _render_legend(L)
