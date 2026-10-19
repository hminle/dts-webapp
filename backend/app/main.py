"""FastAPI application entrypoint."""

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
    weekly,
    yoy,
)
from app.core.duckdb import DataUnavailable


def generate_unique_id(route: APIRoute) -> str:
    """Stable, readable operation ids so the generated TS client stays clean."""
    return f"{route.tags[0]}_{route.name}"


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


for module in (health, meta, lookups, data, net_transfers, weekly, yoy, categories):
    app.include_router(module.router)
