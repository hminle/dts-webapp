"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.routers import health


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

app.include_router(health.router)
