"""CSS matching the "DXF Tool - Maquette" design (IBM Plex type, warm
neutral surfaces, single blue accent), with a light/dark token swap."""

LIGHT = {
    "page": "#F5F4F0", "surface": "#FFFFFF", "ink": "#161714", "muted": "#6B6A63",
    "line": "#DEDCD5", "line-soft": "#EBE9E3", "accent": "#2F5D8C", "accent-hover": "#1F3F60",
    "accent-soft": "#F0F4F8", "dashed": "#C3C0B7", "hatch-a": "#F0EFEA", "hatch-b": "#E7E5DE",
}

DARK = {
    "page": "#131412", "surface": "#1C1D1A", "ink": "#F0EFE9", "muted": "#9A988E",
    "line": "#2E2F2B", "line-soft": "#262723", "accent": "#7FA8CE", "accent-hover": "#A8C4DD",
    "accent-soft": "#1E2830", "dashed": "#3C3D38", "hatch-a": "#232420", "hatch-b": "#1B1C19",
}


def inject(theme: str, rtl: bool) -> str:
    tokens = DARK if theme == "dark" else LIGHT
    css_vars = "\n".join(f"  --{k}: {v};" for k, v in tokens.items())
    direction = "rtl" if rtl else "ltr"
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
{css_vars}
}}

html, body, [data-testid="stAppViewContainer"] {{
  direction: {direction};
  background: var(--page) !important;
  color: var(--ink);
  font-family: 'IBM Plex Sans', sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent; height: 0; min-height: 0; pointer-events: none; }}
[data-testid="stToolbar"] {{ display: none; }}
#MainMenu {{ display: none; }}
[data-testid="stAppViewContainer"] > .main {{ padding-top: 0; }}
.block-container {{ padding-top: 1.25rem; padding-bottom: 2rem; max-width: 100%; }}
[data-testid="stSidebar"] {{
  background: var(--surface);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}

.mono {{ font-family: 'IBM Plex Mono', monospace; }}
.muted {{ color: var(--muted); }}
.dxf-eyebrow {{
  font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: 0.12em;
  color: var(--muted); margin-bottom: 4px;
}}
.dxf-title {{ font-size: 20px; font-weight: 600; letter-spacing: -0.01em; }}

.file-name {{ font-size: 14px; font-weight: 500; display: block; }}
.file-status {{ font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--muted); }}

.stat-big {{ font-size: 34px; font-weight: 600; letter-spacing: -0.02em; line-height: 1; color: var(--accent); }}
.stat-label {{ font-size: 13px; color: var(--muted); margin-bottom: 4px; }}
.stat-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 500; }}

.row-line {{
  display: flex; justify-content: space-between; gap: 16px; padding: 8px 0;
  border-bottom: 1px solid var(--line-soft); font-size: 13px;
}}
.row-line:last-child {{ border-bottom: none; }}
.row-line .k {{ color: var(--muted); }}
.row-line .v {{ font-family: 'IBM Plex Mono', monospace; }}

.legend {{ display: flex; gap: 24px; flex-wrap: wrap; font-size: 13px; color: var(--muted); align-items: center; }}
.legend .swatch {{ width: 12px; height: 12px; display: inline-block; margin-right: 6px; vertical-align: -1px; }}

.dxf-footer {{ padding: 10px 0 0; border-top: 1px solid var(--line); font-size: 12px; color: var(--muted); margin-top: 24px; }}

/* Buttons -> flat outline pills matching the maquette */
div[data-testid="stButton"] > button {{
  border: 1px solid var(--line); border-radius: 3px; background: var(--surface);
  color: var(--muted); font-family: 'IBM Plex Sans', sans-serif; font-size: 13px;
  padding: 7px 16px; box-shadow: none;
}}
div[data-testid="stButton"] > button:hover {{
  color: var(--ink); border-color: var(--dashed); background: var(--surface);
}}
div[data-testid="stButton"] > button:focus:not(:active) {{ box-shadow: none; }}

div.stVerticalBlock[data-test-wrap="false"] {{ border-color: var(--line) !important; border-radius: 3px !important; }}

[data-testid="stFileUploaderDropzone"] {{
  background: transparent; border: 1px dashed var(--dashed) !important; border-radius: 3px;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span, [data-testid="stFileUploaderDropzoneInstructions"] small {{
  color: var(--muted);
}}

[data-testid="stNumberInput"] input {{
  font-family: 'IBM Plex Mono', monospace; background: var(--surface); color: var(--ink);
  border: 1px solid var(--line); border-radius: 3px;
}}

hr {{ border-color: var(--line); }}
</style>
"""


_VARIANTS = {
    "pill_active": "border-color:var(--accent)!important;background:var(--accent-soft)!important;color:var(--accent)!important;",
    "primary": "background:var(--accent)!important;border-color:var(--accent)!important;color:var(--page)!important;font-weight:500!important;",
    "ghost": "border:none!important;background:none!important;padding:0!important;color:var(--muted)!important;",
    "tab_active": "border:none!important;background:none!important;border-radius:0!important;"
                  "border-bottom:2px solid var(--accent)!important;color:var(--ink)!important;font-weight:500!important;",
    "tab_inactive": "border:none!important;background:none!important;border-radius:0!important;"
                     "border-bottom:2px solid transparent!important;color:var(--muted)!important;",
    "card_active": "background:var(--accent-soft)!important;border-color:var(--accent)!important;",
}


def key_style(key: str, variant: str, target: str = "button") -> str:
    """A tiny <style> block applying one of _VARIANTS to the element
    identified by Streamlit's auto-generated `.st-key-<key>` class."""
    css = _VARIANTS[variant]
    selector = f".st-key-{key}" if target == "self" else f".st-key-{key} {target}"
    return f"<style>{selector} {{ {css} }}</style>"
