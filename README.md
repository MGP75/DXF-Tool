# DXF Tool

Streamlit implementation of the "DXF Tool - Maquette" design: upload DXF
cutting files and get the number of plies, usable surface, waste and
estimated mass, plus a nesting visualization.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How it works

- `dxf_engine.py` parses each DXF with `ezdxf`, extracts the closed
  contours ("plies") with `shapely`, and rasterizes the fabric envelope
  into a patch grid to measure usable vs. waste surface.
- `app.py` is the Streamlit UI: file manager sidebar, Data/Visualization
  tabs, binary/gradient nesting plot (Plotly), FR/EN/AR language switch,
  light/dark theme, and a "chips" DXF export.
- `styles.py` / `i18n.py` hold the design tokens and translated strings.
