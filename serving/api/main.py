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

try:
    from cassandra import OperationTimedOut
    from cassandra.cluster import NoHostAvailable
except ImportError:
    class OperationTimedOut(Exception):
        pass

    class NoHostAvailable(Exception):
        pass
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",   # Vite fallback port when 5173 is in use
        "http://127.0.0.1:5174",
        "http://localhost:5175",   # Vite second fallback
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cassandra down ──────────────────────────────────────────────────────────
# A Cassandra router (BR1, BR3, BR5, BR6, BR8) can find the node gone at its
# first connect, or mid-demo after it was up: the session in
# serving/api/cassandra.py is cached, so the driver error then comes from
# execute(). Either way the screen gets a 503 that says what to run, instead of
# a bare 500 it cannot explain.
@app.exception_handler(NoHostAvailable)
@app.exception_handler(OperationTimedOut)
def cassandra_down(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Cassandra is not answering. Run docker compose up -d --wait, "
                           "then python serving/check_infra.py."},
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
