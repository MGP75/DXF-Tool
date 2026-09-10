import streamlit as st
import time
import hashlib
import sys
import base64
import styles

from pathlib import Path

from trad import TEXTS, LANG_ORDER
from main import compute
from draw import build_heatmap_figure
from export_geometry import export_chips_dxf
from ui.css import CssMarker

APP_DIR = Path(__file__).resolve().parent

from sna_df_streamlit_auth_lib import protect_app, protect_function
# from sna_df_streamlit_otel_lib import (
# 	get_otel,
# 	traced_section,
# 	track_page,
# 	instrument_button,
# )
from sna_df_streamlit_matomo_lib import load_matomo_tracking_html

# ===========================================
#                 FUNCTION
# ===========================================

def resolve_resource_path(path_value):
    path_obj = Path(path_value)

    if path_obj.is_absolute() and path_obj.exists():
        return path_obj

    candidates = [
        path_obj,
        APP_DIR / path_obj,
        APP_DIR.parent / path_obj,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return path_obj

def load_css(file_path):
    css_path = resolve_resource_path(file_path)

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    else:
        st.warning(f"CSS file not found: {file_path}")

def render_flag_image(file_path, width=150):
    image_path = resolve_resource_path(file_path)

    if not image_path.exists():
        st.warning(f"Image file not found: {file_path}")
        return

    suffix = image_path.suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    st.markdown(
        (
            f'<img src="data:{mime_type};base64,{encoded_image}" '
            f'alt="" width="{width}" style="display:block;">'
        ),
        unsafe_allow_html=True,
    )

def tr(key):
    return TEXTS[st.session_state.lang][key]

def write_output(text):
    if st.session_state.lang == "ar":
        st.markdown(f'<div class="output-line rtl-output">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="output-line ltr-output">{text}</div>', unsafe_allow_html=True)

def write_title(text):
    if st.session_state.lang == "ar":
        st.markdown(f'<h3 class="rtl-output">{text}</h3>', unsafe_allow_html=True)
    else:
        st.markdown(f"{text}")

def setup_app():

    # ===========================================
    #                 PARSING
    # ===========================================

    st.set_page_config(layout="wide")

    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "results_cache" not in st.session_state:
        st.session_state.results_cache = {}
    if "export_cache" not in st.session_state:
        st.session_state.export_cache = {}
    if "heatmap_mode" not in st.session_state:
        st.session_state.heatmap_mode = "binary"
    if "areal_mass" not in st.session_state:
        st.session_state.areal_mass = 0.0
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if "progress_value" not in st.session_state:
        st.session_state.progress_value = 0

    if st.session_state.theme == "dark":
        load_css("assets/css/dark.css")
    else:
        load_css("assets/css/default.css")

    # ===========================================
    #                 HEADER
    # ===========================================

    top_left, top_btn, top_theme, top_main = st.columns([2, 1, 1, 10])
    # ========= FLAG =========

    with top_left:
        render_flag_image(TEXTS[st.session_state.lang]["flag_path"], width=150)

    # ========= BTN FLAG =========

    with top_btn:

        st.write("")
        if st.button("↻", key="lang_switch"):
            current_index = LANG_ORDER.index(st.session_state.lang)
            next_index = (current_index + 1) % len(LANG_ORDER)
            st.session_state.lang = LANG_ORDER[next_index]
            st.rerun()

    # ========= BTN THEME =========

    with top_theme:
        write_output("")

        theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"

        if st.button(theme_icon, key="theme_switch"):
            if st.session_state.theme == "dark":
                st.session_state.theme = "light"
            else:
                st.session_state.theme = "dark"

            st.rerun()

    # ========= TITLE =========

    with top_main:
        st.markdown(f'<div class="header">{tr("app_title")}</div>', unsafe_allow_html=True)

    # ===========================================
    #                 MAIN PAGE
    # ===========================================

    col_left, col_main = st.columns([1, 3])

    # ============================
    # ========= LEFT CON =========
    # ============================

    with col_left:
        st.markdown(f'<div class="card">{tr("files_zone")}</div>', unsafe_allow_html=True)

    # ========= UPLOADER =========
        uploaded_files = st.file_uploader(
            tr("add_files"),
            type=["dxf"],
            accept_multiple_files=True
        )

    # ========= FILE BTN =========
        if uploaded_files:
            for file in uploaded_files:

                file_bytes = file.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                cache_key = (file.name, file_hash, 0.5, 100)

                already_processed = (
                    cache_key in st.session_state.results_cache
                )

                label = file.name
                if cache_key in st.session_state.results_cache:
                    label = "✅ " + label
                if st.session_state.selected_file == file:
                    label = "▶️ " + label

                if st.button(label=label, key=file.name, width='stretch'):
                    st.session_state.selected_file = file
                    st.rerun()

    # ========= TOTAL BTN =========
        if uploaded_files and len(uploaded_files) >= 2:
            if st.button(tr("total"), key=tr("total"), width='stretch'):
                st.session_state.selected_file = "Total"

    # ============================
    # ========= MAIN CON =========
    # ============================

    with col_main:
        st.markdown(f'<div class="card">{tr("main_zone")}</div>', unsafe_allow_html=True)

    # ========= AREAL MASS =========
        if st.session_state.selected_file == "Total":
            st.session_state.areal_mass = st.number_input(
                tr("areal_mass"),
                min_value=0.0,
                value=float(st.session_state.areal_mass),
                step=10.0,
                key="areal_mass_input"
            )
        elif st.session_state.selected_file is not None and (st.session_state.selected_file.name, hashlib.md5(st.session_state.selected_file.getvalue()).hexdigest(), 0.5, 100) in st.session_state.results_cache:
            st.session_state.areal_mass = st.number_input(
                tr("areal_mass"),
                min_value=0.0,
                value=float(st.session_state.areal_mass),
                step=10.0,
                key="areal_mass_input"
            )

    # ============================
    # ======== TOTAL ALGO ========
    # ============================
        if st.session_state.selected_file == "Total":
            x = time.time()
            result = {
                "geoms": 0,
                "tested": 0,
                "valid": 0,
                "surface": 0,
                "unusable_surface": 0
            }

            progress_file_text = st.empty()
            total_files = len(uploaded_files)
            surface_m2 = 0.0

            progress_text = st.empty()
            progress_bar = st.progress(0)

            st.session_state.progress_value = 0

            def progress_callback_total(value, message):
                progress_bar.progress(min(max((st.session_state.progress_value + value) / total_files, 0), 1))
                progress_text.write(message)
                if value == 1:
                    st.session_state.progress_value += 1

            for i, file in enumerate(uploaded_files, start=0):

                progress_file_text.write(f"{tr("traitement")} : {file.name} | {i}/{total_files}")

                file_bytes = file.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                cache_key = (file.name, file_hash, 0.5, 100)

                if cache_key not in st.session_state.results_cache:
                    st.session_state.results_cache[cache_key] = compute(file, 0.5, 100, progress_callback=progress_callback_total, lang=st.session_state.lang)
                else:
                    progress_callback_total(1, f"File {file.name} already calculated")

                res = st.session_state.results_cache[cache_key]

                result['geoms'] += res['geoms']
                result['tested'] += res['tested']
                result['valid'] += res['valid']
                result['surface'] += res['surface']
                result['unusable_surface'] += res['unusable_surface']
                surface_m2 += res['surface']

            progress_bar.empty()
            progress_text.empty()

            y = time.time()
            tps = y - x
            print(f"{int(tps)}s.{int((tps % 1) * 1000):03d}ms")
            progress_file_text.empty()

            mass = (surface_m2 / 1000000) * st.session_state.areal_mass

    # ======== TOTAL OUTPUT ========
            write_title(f"{tr("total")}")

            write_output(f"{tr("plies_count")} : {result['geoms']}")
            write_output(f"{tr("patch_tested")} : {result['tested']}")
            write_output(f"{tr("patch_valid")} : {result['valid']}")
            if st.session_state.lang != "ar":
                write_output(f"{tr("surface")} : {f'{round(result['surface'], 2):,.2f}'.replace(',',' ')}mm² | {f'{round(result['surface'] / 1000000, 2):,.2f}'.replace(',',' ')}m²")
                write_output(f"{tr("unusable_surface")} : {f'{round(result['unusable_surface'], 2):,.2f}'.replace(',',' ')}mm² | {f'{round(result['unusable_surface'] / 1000000, 2):,.2f}'.replace(',',' ')}m²")
                write_output(f"{tr("percent")} : {f'{round((result["surface"] / (result["surface"] + result["unusable_surface"])) * 100, 2):,.2f}'.replace(',',' ')}%")
                write_output(f"{tr("estimated_mass")} : {f'{round(mass, 2):,.2f}'.replace(',', ' ')} g")
            else:
                write_output(f"{round(result['surface'], 2):,.2f}mm² | {round(result['surface'] / 1000000, 2):,.2f}m² : {tr("surface")}")
                write_output(f"{round(result['unusable_surface'], 2):,.2f}mm² | {round(result['unusable_surface'] / 1000000, 2):,.2f}m² : {tr("unusable_surface")}")
                write_output(f"{round(mass, 2):,.2f}g : {tr("estimated_mass")}")

    # ======== FILE ALGO ========
        elif st.session_state.selected_file is not None:

            x = time.time()

            file = st.session_state.selected_file

            tresh = 0.5
            grid = 100

            file_bytes = file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()

            cache_key = (file.name, file_hash, 0.5, 100)
            result = {}

            if cache_key not in st.session_state.results_cache:
                progress_text = st.empty()
                progress_bar = st.progress(0)

                def progress_callback(value, message):
                    progress_bar.progress(min(max(value, 0), 1))
                    progress_text.write(message)

                st.session_state.results_cache[cache_key] = compute(file, 0.5, 100, progress_callback=progress_callback, lang=st.session_state.lang)

                progress_bar.empty()
                progress_text.empty()

                st.rerun()

            result = st.session_state.results_cache[cache_key]

            y = time.time()
            tps = y - x
            print(f"{int(tps)}s.{int((tps % 1) * 1000):03d}ms")

            surface_m2 = result["surface"] / 1000000
            mass = surface_m2 * st.session_state.areal_mass

    # ======== FILE OUTPUT ========
            write_title(f"{file.name}")

            write_output(f"{tr("plies_count")} : {result['geoms']}")
            write_output(f"{tr("patch_tested")} : {result['tested']}")
            write_output(f"{tr("patch_valid")} : {result['valid']}")
            if st.session_state.lang != "ar":
                write_output(f"{tr("surface")} : {f'{round(result['surface'], 2):,.2f}'.replace(',',' ')}mm² | {f'{round(result['surface'] / 1000000, 2):,.2f}'.replace(',',' ')}m²")
                write_output(f"{tr("unusable_surface")} : {f'{round(result['unusable_surface'], 2):,.2f}'.replace(',',' ')}mm² | {f'{round(result['unusable_surface'] / 1000000, 2):,.2f}'.replace(',',' ')}m²")
                write_output(f"{tr("percent")} : {f'{round((result["surface"] / (result["surface"] + result["unusable_surface"])) * 100, 2):,.2f}'.replace(',',' ')}%")
                write_output(f"{tr("estimated_mass")} : {f'{round(mass, 2):,.2f}'.replace(',', ' ')} g")
            else:
                write_output(f"{round(result['surface'], 2):,.2f}mm² | {round(result['surface'] / 1000000, 2):,.2f}m² : {tr("surface")}")
                write_output(f"{round(result['unusable_surface'], 2):,.2f}mm² | {round(result['unusable_surface'] / 1000000, 2):,.2f}m² : {tr("unusable_surface")}")
                write_output(f"{f'{round((result["surface"] / (result["surface"] + result["unusable_surface"])) * 100, 2):,.2f}'.replace(',',' ')}% : {tr("percent")}")
                write_output(f"{round(mass, 2):,.2f}g : {tr("estimated_mass")}")

            col_mode1, col_mode2 = st.columns(2)

    # ======== BINARY VISU ========
            with col_mode1:
                if st.button(tr("binary"), key=tr("binary"), use_container_width=True):
                    st.session_state.heatmap_mode = "binary"

    # ======== HEATMAP VISU ========
            with col_mode2:
                if st.button(tr("gradient"), key=tr("gradient"), use_container_width=True):
                    st.session_state.heatmap_mode = "gradient"

    # ======== RENDU VISU ========
            fig = build_heatmap_figure(result=result, mode=st.session_state.heatmap_mode)
            st.plotly_chart(fig, width='stretch')

    # ======== EXPORT BTN ========
            export_payload = st.session_state.export_cache.get(cache_key)
            if export_payload is None:
                export_payload = export_chips_dxf(file, result)
                st.session_state.export_cache[cache_key] = export_payload

            st.download_button(
                tr("chips_export"),
                data=export_payload["data"],
                file_name=export_payload["file_name"],
                mime="application/dxf",
                key="chips_export_download",
                use_container_width=True,
            )

    # ======== DEFAULT TEXT ========
        else:
            write_output(tr("click_file"))

        st.markdown('</div>', unsafe_allow_html=True)

def main():

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        setup_app()
    else:
        protect_app(setup_app, "sna-di-methodes-dxf-tool-user", "DXF Tool")

    # Matomo tracking (optional, ignore errors if MATOMO_SITE_ID not set)
    try:
        html = load_matomo_tracking_html(
            privacy_mentions_url="https://safranna.pages.cloud.safran/snasodifdevops/snadifknowledge/samples/unknowprojectnamepoc/pages/privacy/privacy.html",
            privacy_link_style="color:#111;font-weight:700;text-decoration:none;"
        )
        st.iframe(html)
    except ValueError:
        pass

if __name__ == "__main__":
    main()
