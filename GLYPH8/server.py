"""
TRANSMISSION — Glyph Structural Constraint Engine
Web API and static file server for the GLYPH8 system.
Render deployment entry point.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
import json

# Import the constraint engine
from glyph_constraint import (
    MappingRule, construct_partitions, compute_structural_constraint_ratio,
    classify_zone, LOWER_THRESHOLD, UPPER_THRESHOLD, REFERENCE_POINT,
    SCHEMA_VERSION, SUBORDINATED, STRUCTURAL, DOMINANT
)

app = FastAPI(
    title="TRANSMISSION",
    description="Glyph Structural Constraint Engine — Heyer Livin LLC",
    version="1.0.0"
)

BASE = Path(__file__).parent
# Full clone includes repo root; GitHub Pages / your plan often use root `index.html`
# (e.g. Interactive Data Simulator). Render `rootDir` is GLYPH8 only, but parent paths exist.
REPO_ROOT = BASE.parent

# ── API Routes ──────────────────────────────────────────────────────

@app.get("/health")
def health_render():
    """Minimal check for Render health probes (and load balancers)."""
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {
        "status": "live",
        "engine": "GLYPH8",
        "schema_version": SCHEMA_VERSION,
        "thresholds": {
            "lower": LOWER_THRESHOLD,
            "upper": UPPER_THRESHOLD,
            "reference": REFERENCE_POINT
        }
    }

@app.post("/api/compute")
async def compute(request: Request):
    """
    Accept x and y values, compute structural constraint ratio,
    classify zone, return full result.
    """
    body = await request.json()
    x = float(body.get("x", 0))
    y = float(body.get("y", 0))

    if x < 0 or y < 0:
        return JSONResponse(status_code=400, content={"error": "x and y must be non-negative"})
    if x == 0 and y == 0:
        return JSONResponse(status_code=400, content={"error": "x and y cannot both be zero"})

    denom = x + (y ** 2)
    ratio = x / denom if denom != 0 else 0
    zone = classify_zone(ratio)

    return {
        "x": x,
        "y": y,
        "ratio": round(ratio, 6),
        "zone": zone,
        "thresholds": {
            "lower": LOWER_THRESHOLD,
            "upper": UPPER_THRESHOLD,
            "reference": REFERENCE_POINT
        },
        "interpretation": {
            SUBORDINATED: "Below structural floor — system is subordinated",
            STRUCTURAL: "Within structural band — constraint attractor active",
            DOMINANT: "Above structural ceiling — dominant position"
        }.get(zone, "Unknown")
    }

@app.get("/api/schema")
def schema():
    schema_path = BASE / "event_schema_v1.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return {"error": "schema not found"}

# ── Static files (HTML pages, PDFs, etc.) ───────────────────────────

# Serve subdirectories
for subdir in ["app", "shop", "patent", "research", "deck", "pitch", "blueprint", "docs"]:
    dirpath = BASE / subdir
    if dirpath.is_dir():
        app.mount(f"/{subdir}", StaticFiles(directory=str(dirpath), html=True), name=subdir)

# Root index — prefer repo-root simulator / landing (matches GitHub default), else GLYPH8
@app.get("/", response_class=HTMLResponse)
def root():
    for candidate in (REPO_ROOT / "index.html", BASE / "index.html"):
        if candidate.is_file():
            return HTMLResponse(candidate.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>TRANSMISSION</h1><p>Engine running.</p>")

# Catch-all for static files (repo root first, then GLYPH8)
@app.get("/{filename:path}")
async def static_file(filename: str):
    if filename.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "not found"})
    for root in (REPO_ROOT, BASE):
        filepath = (root / filename).resolve()
        try:
            root_resolved = root.resolve()
            if filepath.is_file() and filepath.is_relative_to(root_resolved):
                return FileResponse(filepath)
        except (OSError, ValueError):
            continue
    return JSONResponse(status_code=404, content={"error": "not found"})
