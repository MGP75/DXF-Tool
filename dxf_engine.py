"""DXF parsing and nesting analysis.

Reads a DXF cutting file, extracts the closed contours ("plies"), builds a
patch grid over the fabric envelope to measure how much of it is covered by
usable material, and can re-export the DXF with small "chip" markers placed
on every usable patch.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field

import ezdxf
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

MAX_GRID_CELLS = 45_000  # keeps the heatmap responsive for large drawings
CHIP_LAYER = "CHIPS"


@dataclass
class DxfAnalysis:
    name: str
    size_bytes: int
    plies: int
    patches_tested: int
    patches_usable: int
    usable_mm2: float
    waste_mm2: float
    envelope_mm2: float
    saved_pct: float
    grid_x: np.ndarray  # patch center x-coordinates (nx,)
    grid_y: np.ndarray  # patch center y-coordinates (ny,)
    grid_z: np.ndarray  # coverage fraction per patch, shape (ny, nx), 0..1
    bounds: tuple[float, float, float, float]  # minx, miny, maxx, maxy
    polygons: list[list[tuple[float, float]]] = field(default_factory=list)

    def usable_m2(self) -> float:
        return self.usable_mm2 / 1_000_000

    def waste_m2(self) -> float:
        return self.waste_mm2 / 1_000_000

    def mass_grams(self, areal_mass_g_per_m2: float) -> float:
        return self.usable_m2() * areal_mass_g_per_m2


def _closed_polygons_from_modelspace(msp) -> list[Polygon]:
    polygons: list[Polygon] = []

    for e in msp.query("LWPOLYLINE"):
        if not e.closed:
            continue
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) >= 3:
            polygons.append(pts)

    for e in msp.query("POLYLINE"):
        if not e.is_closed:
            continue
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if len(pts) >= 3:
            polygons.append(pts)

    for e in msp.query("CIRCLE"):
        c = e.dxf.center
        r = e.dxf.radius
        if r > 0:
            polygons.append(Point(c.x, c.y).buffer(r, resolution=24))

    valid: list[Polygon] = []
    for p in polygons:
        try:
            poly = p if isinstance(p, Polygon) else Polygon(p)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.geom_type == "Polygon" and poly.area > 1e-6:
                valid.append(poly)
        except Exception:
            continue
    return valid


def _envelope_polygon(polygons: list[Polygon]) -> tuple[Polygon, list[Polygon]]:
    """The fabric roll boundary: the largest contour that contains the rest,
    falling back to the overall bounding box when no such frame is found.
    Returns (envelope, cut_parts) where cut_parts excludes the frame itself."""
    by_area = sorted(polygons, key=lambda p: p.area, reverse=True)
    biggest = by_area[0]
    others = by_area[1:]
    if others and all(biggest.covers(p.buffer(-1e-6)) for p in others):
        return biggest, others

    union = unary_union(polygons)
    minx, miny, maxx, maxy = union.bounds
    envelope = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)])
    return envelope, polygons


def _build_grid(envelope: Polygon, parts: list[Polygon], progress=None):
    minx, miny, maxx, maxy = envelope.bounds
    width, height = maxx - minx, maxy - miny
    if width <= 0 or height <= 0:
        raise ValueError("empty drawing envelope")

    aspect = width / height
    ny = max(1, int(math.sqrt(MAX_GRID_CELLS / aspect)))
    nx = max(1, int(MAX_GRID_CELLS / ny))

    xs = minx + (np.arange(nx) + 0.5) * (width / nx)
    ys = miny + (np.arange(ny) + 0.5) * (height / ny)

    union_parts = prep(unary_union(parts)) if parts else None
    prepared_env = prep(envelope)

    z = np.zeros((ny, nx), dtype=np.float32)
    tested = 0
    usable = 0
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            pt = Point(x, y)
            if not prepared_env.intersects(pt):
                continue
            tested += 1
            if union_parts is not None and union_parts.intersects(pt):
                z[j, i] = 1.0
                usable += 1
        if progress is not None and ny > 1:
            progress(0.15 + 0.75 * (j + 1) / ny, "step_patch")

    return xs, ys, z, tested, usable


def analyze_bytes(name: str, data: bytes, progress=None) -> DxfAnalysis:
    """progress(fraction: float, step_key: str) is called repeatedly as the
    analysis moves through its phases, mirroring the maquette's step list."""
    if progress is None:
        progress = lambda *_: None

    progress(0.02, "step_read")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    try:
        doc = ezdxf.read(io.StringIO(text))
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"malformed DXF structure ({exc})") from None
    progress(0.10, "step_read")

    msp = doc.modelspace()
    polygons = _closed_polygons_from_modelspace(msp)
    if not polygons:
        raise ValueError("no closed contour found in this DXF file")
    progress(0.15, "step_extract")

    envelope, parts = _envelope_polygon(polygons)
    xs, ys, z, tested, usable = _build_grid(envelope, parts, progress=progress)
    progress(0.95, "step_measure")

    usable_mm2 = sum(p.area for p in parts)
    envelope_mm2 = envelope.area
    waste_mm2 = max(envelope_mm2 - usable_mm2, 0.0)
    saved_pct = (usable_mm2 / envelope_mm2 * 100) if envelope_mm2 else 0.0

    return DxfAnalysis(
        name=name,
        size_bytes=len(data),
        plies=len(parts),
        patches_tested=tested,
        patches_usable=usable,
        usable_mm2=usable_mm2,
        waste_mm2=waste_mm2,
        envelope_mm2=envelope_mm2,
        saved_pct=saved_pct,
        grid_x=xs,
        grid_y=ys,
        grid_z=z,
        bounds=envelope.bounds,
        polygons=[list(p.exterior.coords) for p in parts],
    )


def combine(analyses: list[DxfAnalysis]) -> dict:
    """Aggregate stats across several files for the "Total" view."""
    usable_mm2 = sum(a.usable_mm2 for a in analyses)
    waste_mm2 = sum(a.waste_mm2 for a in analyses)
    envelope_mm2 = sum(a.envelope_mm2 for a in analyses)
    return {
        "plies": sum(a.plies for a in analyses),
        "patches_tested": sum(a.patches_tested for a in analyses),
        "patches_usable": sum(a.patches_usable for a in analyses),
        "usable_mm2": usable_mm2,
        "waste_mm2": waste_mm2,
        "envelope_mm2": envelope_mm2,
        "saved_pct": (usable_mm2 / envelope_mm2 * 100) if envelope_mm2 else 0.0,
    }


def export_with_chips(original_bytes: bytes, analysis: DxfAnalysis) -> bytes:
    """Return a copy of the DXF with a small cross ("chip") stamped at the
    center of every usable patch, on a dedicated CHIPS layer."""
    try:
        text = original_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = original_bytes.decode("latin-1")
    doc = ezdxf.read(io.StringIO(text))

    if CHIP_LAYER not in doc.layers:
        doc.layers.add(CHIP_LAYER, color=1)
    msp = doc.modelspace()

    xs, ys, z = analysis.grid_x, analysis.grid_y, analysis.grid_z
    if len(xs) > 1:
        half_w = (xs[1] - xs[0]) * 0.3
    else:
        half_w = 1.0
    if len(ys) > 1:
        half_h = (ys[1] - ys[0]) * 0.3
    else:
        half_h = 1.0

    for j, y in enumerate(ys):
        row = z[j]
        for i, x in enumerate(xs):
            if row[i] <= 0:
                continue
            msp.add_line((x - half_w, y), (x + half_w, y), dxfattribs={"layer": CHIP_LAYER})
            msp.add_line((x, y - half_h), (x, y + half_h), dxfattribs={"layer": CHIP_LAYER})

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")
