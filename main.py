"""Adapts the real DXF analysis engine (dxf_engine.py, ezdxf + shapely) to
the `compute(file, tresh, grid, progress_callback, lang)` entry point used
by app.py, and flattens the result into the plain dict the UI expects."""
from __future__ import annotations

from typing import Any, Callable

import dxf_engine as engine

STEP_KEYS = ("step_read", "step_extract", "step_patch", "step_measure")
_STEP_LABELS = {
    "fr": {"step_read": "Lecture du fichier", "step_extract": "Extraction des entités DXF",
           "step_patch": "Test des patchs", "step_measure": "Calcul des surfaces"},
    "en": {"step_read": "Reading file", "step_extract": "Extracting DXF entities",
           "step_patch": "Testing patches", "step_measure": "Computing surfaces"},
    "ar": {"step_read": "قراءة الملف", "step_extract": "استخراج عناصر DXF",
           "step_patch": "اختبار الرقع", "step_measure": "حساب المساحات"},
}


def compute(
    file: Any,
    tresh: float,
    grid: int,
    progress_callback: Callable[[float, str], None] | None = None,
    lang: str = "en",
) -> dict:
    """tresh/grid mirror the maquette's original cache-key parameters; the
    engine's patch grid is sized automatically, so they aren't threaded any
    further for now."""
    if progress_callback is None:
        progress_callback = lambda *_: None

    labels = _STEP_LABELS.get(lang, _STEP_LABELS["en"])

    def on_progress(fraction: float, step_key: str) -> None:
        progress_callback(min(max(fraction, 0.0), 1.0), labels.get(step_key, step_key))

    name = file.name
    data = file.getvalue()
    analysis = engine.analyze_bytes(name, data, progress=on_progress)
    progress_callback(1.0, labels["step_measure"])

    return {
        "geoms": analysis.plies,
        "tested": analysis.patches_tested,
        "valid": analysis.patches_usable,
        "surface": analysis.usable_mm2,
        "unusable_surface": analysis.waste_mm2,
        "_analysis": analysis,
        "_file_bytes": data,
        "_file_name": name,
    }
