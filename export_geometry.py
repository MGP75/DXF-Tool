"""Re-exports the analyzed DXF with "chip" markers stamped on every usable
patch, for the download button in the file view."""
from __future__ import annotations

from typing import Any

import dxf_engine as engine


def export_chips_dxf(file: Any, result: dict) -> dict:
    analysis = result["_analysis"]
    original_bytes = result.get("_file_bytes") or file.getvalue()
    data = engine.export_with_chips(original_bytes, analysis)
    file_name = analysis.name.rsplit(".", 1)[0] + "_chips.dxf"
    return {"data": data, "file_name": file_name}
