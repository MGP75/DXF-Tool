"""Color tokens for the light/dark theme, shared by the Plotly heatmap
(draw.py) and the deferred widget-state CSS (ui/css.py).

The page's own stylesheet is loaded directly from assets/css/dark.css or
assets/css/default.css by app.py, so this module only holds Python-side
values: the token dicts and the small per-widget CSS snippets below."""
from __future__ import annotations

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
