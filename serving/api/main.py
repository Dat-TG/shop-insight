"""ShopInsight FastAPI application entry point.

Run (from repo root, with .venv activated):
    uvicorn serving.api.main:app --reload --port 8000

Development:
    http://localhost:8000/health    → {"status": "ok"}
    http://localhost:8000/docs      → Swagger UI (auto-generated from routers)
    http://localhost:8000/api/br2/funnel

Adding a new BR:
    1. Create serving/api/routers/br<N>.py
    2. from serving.api.routers import br<N>
    3. app.include_router(br<N>.router)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serving.api.routers import br1, br2, br3, br4, br5, br6, br7, br8

app = FastAPI(
    title="ShopInsight API",
    description=(
        "Group 15 — CO5173 Data Engineering.\n\n"
        "Each `/api/brN/` prefix is owned by one team member. "
        "All endpoints return `{ data: [], meta: {} }` so the React "
        "QueryMeta component works identically on every screen."
    ),
    version="0.1.0",
)

# ── CORS ────────────────────────────────────────────────────────────────────
# Allow the Vite dev server (port 5173) to call the API.
# In production, replace "*" with the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers — one per BR ────────────────────────────────────────────────────
app.include_router(br1.router)
app.include_router(br2.router)
app.include_router(br3.router)
app.include_router(br4.router)
app.include_router(br5.router)
app.include_router(br6.router)
app.include_router(br7.router)
app.include_router(br8.router)


# ── Health ──────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    """Liveness probe. Returns ``{"status": "ok"}`` when the server is up."""
    return {"status": "ok"}
