"""Application settings loaded from the environment (prefix ``APP_``)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved from this file, not the working directory: on Vercel the cwd is the
# project base, which is not guaranteed to be backend/.
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    duckdb_path: Path = BACKEND_DIR / "data" / "treasury_data.duckdb"
    artifact_url: str | None = None

    # Ingestion only. The reference app declared these but its client read
    # module constants instead, so .env overrides never took effect.
    treasury_base_url: str = (
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
    )
    api_page_size: int = 10000
    api_throttle_time: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()
