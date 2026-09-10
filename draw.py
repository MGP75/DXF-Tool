"""Builds the nesting heatmap figure shown for the currently selected file."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import styles


def build_heatmap_figure(result: dict, mode: str = "binary") -> go.Figure:
    analysis = result["_analysis"]
    tokens = styles.DARK if st.session_state.get("theme") == "dark" else styles.LIGHT

    if mode == "binary":
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
        margin=dict(l=10, r=10, t=20, b=10), height=460,
        xaxis=dict(scaleanchor="y", showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    )
    return fig
