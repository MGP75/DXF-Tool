"""DXF Tool — Streamlit implementation of the "DXF Tool - Maquette" design.

Upload one or more DXF cutting files; the app parses their closed contours,
runs a patch-grid nesting test against the fabric envelope, and reports the
usable surface, waste and estimated mass. Real analysis via ezdxf + shapely.
"""
from __future__ import annotations

import hashlib

import plotly.graph_objects as go
import streamlit as st

import dxf_engine as engine
import styles
from i18n import t

st.set_page_config(page_title="DXF Tool", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------- state ----
defaults = {
    "theme": "light",
    "lang": "fr",
    "page": "viz",
    "view": "binary",
    "areal_mass": 204.0,
    "files": {},       # file_id -> {name, size, bytes, status, analysis, error}
    "order": [],        # upload order of file_ids
    "selected": None,   # file_id or "__total__"
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

L = st.session_state.lang
# Base styling (fonts, colors, hiding Streamlit chrome) is injected right
# away so the page never flashes unstyled while a file is being analyzed.
st.markdown(styles.inject(st.session_state.theme, rtl=(L == "ar")), unsafe_allow_html=True)

# Per-key "active state" rules depend on widgets rendered further down, so
# they're gathered here and flushed together (see flush_css) once computed.
# A <style> tag applies globally regardless of where it sits in the DOM.
css_blocks: list[str] = []


def mark(key: str, variant: str, target: str = "button") -> None:
    css_blocks.append(styles.key_style(key, variant, target))


def flush_css() -> None:
    st.markdown("\n".join(css_blocks), unsafe_allow_html=True)


def analyze_new_file(name: str, data: bytes) -> tuple[str, engine.DxfAnalysis | None, str | None]:
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


# ------------------------------------------------------------- callbacks ----
def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"


def do_reset():
    st.session_state.files = {}
    st.session_state.order = []
    st.session_state.selected = None
    st.session_state.page = "viz"
    st.session_state.chip_cache = {}
    # Swaps in a fresh file_uploader widget so previously dropped files don't
    # get silently re-ingested on the next run (the widget keeps its own state).
    st.session_state.uploader_version = st.session_state.get("uploader_version", 0) + 1


def set_lang(code: str):
    st.session_state.lang = code


def select_file(fid: str):
    st.session_state.selected = fid


# ------------------------------------------------------------------ header --
h_left, h_right = st.columns([3, 5])
with h_left:
    st.markdown(
        f"<div style='display:flex;align-items:baseline;gap:14px;padding-top:6px'>"
        f"<span class='dxf-title'>{t(L,'app_name')}</span>"
        f"<span class='mono muted' style='font-size:13px'>{t(L,'version')}</span></div>",
        unsafe_allow_html=True,
    )
with h_right:
    c_fr, c_en, c_ar, c_theme, c_reset, c_user = st.columns([1, 1, 1, 1.8, 2, 2.6])
    for code, col, label in [("fr", c_fr, "FR"), ("en", c_en, "EN"), ("ar", c_ar, "AR")]:
        with col:
            st.button(label, key=f"lang_{code}", on_click=set_lang, args=(code,), use_container_width=True)
        if L == code:
            mark(f"lang_{code}", "pill_active")
    with c_theme:
        st.button(
            t(L, "theme_to_dark") if st.session_state.theme == "light" else t(L, "theme_to_light"),
            key="theme_toggle", on_click=toggle_theme, use_container_width=True,
        )
    with c_reset:
        st.button(t(L, "reset"), key="reset_btn", on_click=do_reset, use_container_width=True)
        mark("reset_btn", "ghost")
    with c_user:
        st.markdown(
            "<div class='muted' style='text-align:right;padding-top:8px;font-size:14px'>maxence.gendrot@safrangroup.com</div>",
            unsafe_allow_html=True,
        )
st.markdown("<hr style='margin:8px 0 16px'>", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar --
with st.sidebar:
    st.markdown(f"<div class='dxf-eyebrow'>{t(L,'files_header')}</div>", unsafe_allow_html=True)

    for fid in st.session_state.order:
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
            st.button(t(L, "select_file"), key=f"pick_{fid}", on_click=select_file, args=(fid,), use_container_width=True)
        if st.session_state.selected == fid:
            mark(f"file_{fid}", "card_active", target="self")

    analyzed = [st.session_state.files[f]["analysis"] for f in st.session_state.order if st.session_state.files[f]["status"] == "analyzed"]
    if len(analyzed) >= 2:
        with st.container(border=True, key="file_total"):
            st.markdown(
                f"<span class='file-name'>{t(L,'total_files', n=len(analyzed))}</span>"
                f"<span class='file-status'>{t(L,'cumulative')}</span>",
                unsafe_allow_html=True,
            )
            st.button(t(L, "select_file"), key="pick_total", on_click=select_file, args=("__total__",), use_container_width=True)
        if st.session_state.selected == "__total__":
            mark("file_total", "card_active", target="self")

    uploader_version = st.session_state.get("uploader_version", 0)
    uploaded = st.file_uploader(
        t(L, "drop_file"), type=["dxf"], accept_multiple_files=True, key=f"uploader_{uploader_version}",
    )
    st.caption(t(L, "browse"))

    def make_fid(name: str, size: int) -> str:
        # A plain slug (not the raw name) so it can double as a Streamlit
        # widget/container key: Streamlit sanitizes keys into CSS classes,
        # and only a key that is already "safe" is guaranteed to match the
        # `.st-key-<key>` selectors used for the active-state styling below.
        digest = hashlib.md5(f"{name}:{size}".encode()).hexdigest()[:12]
        return f"f{digest}"

    if uploaded:
        new_files = [f for f in uploaded if make_fid(f.name, f.size) not in st.session_state.files]
        for f in new_files:
            fid = make_fid(f.name, f.size)
            data = f.getvalue()
            st.session_state.files[fid] = {"name": f.name, "size": f.size, "bytes": data, "status": "pending", "analysis": None, "error": None}
            st.session_state.order.append(fid)
            status, analysis, error = analyze_new_file(f.name, data)
            st.session_state.files[fid].update(status=status, analysis=analysis, error=error)
            if st.session_state.selected is None:
                st.session_state.selected = fid
        if new_files:
            st.rerun()

# -------------------------------------------------------------- main area --
sel = st.session_state.selected

if sel is None:
    st.markdown(
        f"<div style='padding:64px 16px'>"
        f"<div style='font-size:22px;font-weight:500;margin-bottom:12px'>{t(L,'empty_title')}</div>"
        f"<p class='muted' style='max-width:520px;font-size:15px;line-height:1.5'>{t(L,'empty_body')}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    flush_css()
    st.stop()

analysis = None
if sel == "__total__":
    stats = engine.combine(analyzed)
    active_name = t(L, "total_files", n=len(analyzed))
else:
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
        flush_css()
        st.stop()
    if entry["status"] != "analyzed":
        st.info(t(L, "loading_title"))
        flush_css()
        st.stop()
    analysis = entry["analysis"]
    stats = {
        "plies": analysis.plies, "patches_tested": analysis.patches_tested,
        "patches_usable": analysis.patches_usable, "usable_mm2": analysis.usable_mm2,
        "waste_mm2": analysis.waste_mm2, "envelope_mm2": analysis.envelope_mm2,
        "saved_pct": analysis.saved_pct,
    }

# header row: file name, tabs, export button
top_l, top_r = st.columns([3, 1.4])
with top_l:
    name_col, tab1_col, tab2_col = st.columns([2, 1, 1.6])
    with name_col:
        st.markdown(f"<div style='font-size:16px;font-weight:600;padding-top:6px'>{active_name}</div>", unsafe_allow_html=True)
    with tab1_col:
        if st.button(t(L, "tab_data"), key="tab_data_btn", use_container_width=True):
            st.session_state.page = "data"
            st.rerun()
    with tab2_col:
        if analysis is not None:
            if st.button(t(L, "tab_viz"), key="tab_viz_btn", use_container_width=True):
                st.session_state.page = "viz"
                st.rerun()
with top_r:
    if analysis is not None:
        chip_cache = st.session_state.setdefault("chip_cache", {})
        if sel not in chip_cache:
            chip_cache[sel] = engine.export_with_chips(st.session_state.files[sel]["bytes"], analysis)
        chip_bytes = chip_cache[sel]
        st.download_button(
            t(L, "export_btn"), data=chip_bytes,
            file_name=active_name.rsplit(".", 1)[0] + "_chips.dxf",
            mime="application/dxf", use_container_width=True, key="export_btn",
        )
        mark("export_btn", "primary")

page = st.session_state.page if analysis is not None else "data"
mark("tab_data_btn", "tab_active" if page == "data" else "tab_inactive")
if analysis is not None:
    mark("tab_viz_btn", "tab_active" if page == "viz" else "tab_inactive")

st.markdown("<hr>", unsafe_allow_html=True)

if page == "viz" and analysis is not None:
    seg_a, seg_b, _ = st.columns([1, 1.3, 4])
    with seg_a:
        if st.button(t(L, "view_binary"), key="view_binary_btn", use_container_width=True):
            st.session_state.view = "binary"
            st.rerun()
    with seg_b:
        if st.button(t(L, "view_gradient"), key="view_gradient_btn", use_container_width=True):
            st.session_state.view = "gradient"
            st.rerun()
    mark("view_binary_btn", "pill_active" if st.session_state.view == "binary" else "tab_inactive", target="button")
    mark("view_gradient_btn", "pill_active" if st.session_state.view == "gradient" else "tab_inactive", target="button")

    tokens = styles.DARK if st.session_state.theme == "dark" else styles.LIGHT
    z = analysis.grid_z
    if st.session_state.view == "binary":
        colorscale = [[0, tokens["dashed"]], [0.999, tokens["dashed"]], [1, tokens["accent"]]]
        showscale = False
    else:
        colorscale = [[0, tokens["dashed"]], [1, tokens["accent"]]]
        showscale = True

    fig = go.Figure(
        data=go.Heatmap(
            z=z, x=analysis.grid_x, y=analysis.grid_y,
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
        title=dict(text=t(L, "canvas_caption", tested=f"{analysis.patches_tested:,}".replace(",", " "),
                          usable=f"{analysis.patches_usable:,}".replace(",", " ")),
                    font=dict(size=13)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    st.markdown(
        f"<div class='legend'>"
        f"<span><span class='swatch' style='background:var(--accent)'></span>{t(L,'legend_usable')}</span>"
        f"<span><span class='swatch' style='background:var(--dashed)'></span>{t(L,'legend_waste')}</span>"
        f"<span><span class='swatch' style='border:1px solid var(--ink);background:transparent'></span>{t(L,'legend_envelope')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

else:
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

    def fmt_int(n: int) -> str:
        return f"{n:,}".replace(",", " ")

    def fmt_mm2(v: float) -> str:
        return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " mm²"

    rows = [
        (t(L, "plies"), fmt_int(stats["plies"])),
        (t(L, "tested"), fmt_int(stats["patches_tested"])),
        (t(L, "usable_patches"), fmt_int(stats["patches_usable"])),
        (t(L, "usable_surface_mm"), fmt_mm2(stats["usable_mm2"])),
        (t(L, "waste_surface_mm"), fmt_mm2(stats["waste_mm2"])),
    ]
    rows_html = "".join(f"<div class='row-line'><span class='k'>{k}</span><span class='v'>{v}</span></div>" for k, v in rows)
    st.markdown(f"<div style='border-top:1px solid var(--line);padding-top:4px'>{rows_html}</div>", unsafe_allow_html=True)

st.markdown(f"<div class='dxf-footer'>{t(L,'footer')}</div>", unsafe_allow_html=True)
flush_css()
