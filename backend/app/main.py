"""FastAPI application entrypoint."""

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.routers import (
    categories,
    data,
    health,
    lookups,
    meta,
    net_transfers,
    rolling,
    snapshot,
    weekly,
    yoy,
)
from app.core.config import get_settings
from app.core.duckdb import DataUnavailable
from app.mcp_server.server import build_server


def generate_unique_id(route: APIRoute) -> str:
    """Stable, readable operation ids so the generated TS client stays clean."""
    return f"{route.tags[0]}_{route.name}"


settings = get_settings()
if settings.sentry_dsn:
    # Errors only: tracing would add a sampled span per request for no use yet.
    sentry_sdk.init(
        dsn=settings.sentry_dsn, traces_sample_rate=0.0, send_default_pii=False
    )

app = FastAPI(
    title="DTS Analysis API",
    generate_unique_id_function=generate_unique_id,
    # Under /api so Vercel's /api/* rewrite reaches them; /docs would hit the
    # frontend service.
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.exception_handler(DataUnavailable)
def data_unavailable(request: Request, exc: DataUnavailable) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Data is not loaded yet"})


@app.exception_handler(ValueError)
def bad_request(request: Request, exc: ValueError) -> JSONResponse:
    # Services raise ValueError for inputs they reject (unknown data source,
    # same fiscal year twice, bad comparison_mode); the message is for people.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


for module in (
    health,
    meta,
    lookups,
    data,
    net_transfers,
    weekly,
    snapshot,
    rolling,
    yoy,
    categories,
):
    app.include_router(module.router)

# Mounted last so every /api/v1 route matches first. Stateless: each request
# stands alone, so any Fluid compute instance can serve it.
mcp_app = build_server(app).http_app(path="/", stateless_http=True)
# The MCP session manager starts in this lifespan, and Starlette ignores the
# lifespans of mounted apps, so the FastAPI app has to run it.
app.router.lifespan_context = mcp_app.lifespan
app.mount("/api/mcp", mcp_app)
