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


@lru_cache
def get_settings() -> Settings:
    return Settings()
