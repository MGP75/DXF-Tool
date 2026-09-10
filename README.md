# DXF Tool

Streamlit app: upload DXF cutting files and get the number of plies, usable
surface, waste and estimated mass, plus a nesting visualization.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py dev
```

`dev` skips the internal Safran auth wrapper (`sna_df_streamlit_auth_lib`),
which requires the company's private package index and isn't installable
outside that environment.

## How it works

- `dxf_engine.py` parses each DXF with `ezdxf`, extracts the closed
  contours ("plies") with `shapely`, and rasterizes the fabric envelope
  into a patch grid to measure usable vs. waste surface.
- `main.py` adapts that engine to the `compute(file, tresh, grid,
  progress_callback, lang)` entry point used by the UI.
- `draw.py` builds the binary/gradient nesting heatmap (Plotly).
- `export_geometry.py` re-exports the DXF with "chip" markers stamped on
  every usable patch.
- `trad.py` holds the FR/EN/AR strings and the language cycle order.
- `styles.py` holds the light/dark color tokens (used by the heatmap and by
  `ui/css.py`'s per-widget active-state CSS). The page's own stylesheet is
  plain CSS loaded straight from `assets/css/dark.css` / `default.css` —
  no Python templating.
- `app.py` is the Streamlit UI: file manager, FR/EN/AR language switch,
  light/dark theme, single/aggregate ("Total") analysis, and the chips
  export.
