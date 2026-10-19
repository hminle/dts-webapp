"""Download the data artifact into ``data/`` at build time.

Vercel runs this after installing dependencies (``[tool.vercel.scripts] build``),
so the file is bundled with the function and each deploy serves one immutable
snapshot. Run locally the same way:

    uv run python -m scripts.fetch_artifact
"""

import os
import shutil
import sys
import urllib.request

import duckdb

from app.core.config import get_settings


def main() -> int:
    settings = get_settings()
    url = settings.artifact_url
    if not url:
        # Not configured yet is a valid state: the deploy works and /api/health
        # reports data_loaded=false. A configured URL that fails is not.
        print("fetch_artifact: APP_ARTIFACT_URL not set, skipping download")
        return 0

    dest = settings.duckdb_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".download")
    try:
        with urllib.request.urlopen(url, timeout=120) as response, tmp.open("wb") as f:
            shutil.copyfileobj(response, f)
        conn = duckdb.connect(str(tmp), read_only=True)
        try:
            row = conn.execute(
                "SELECT value FROM metadata WHERE key = 'latest_record_date'"
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            raise ValueError("metadata has no latest_record_date")
    except Exception as exc:  # any failure must fail the build, loudly
        tmp.unlink(missing_ok=True)
        print(f"fetch_artifact: artifact rejected: {exc}", file=sys.stderr)
        return 1

    size = tmp.stat().st_size
    os.replace(tmp, dest)
    print(f"fetch_artifact: downloaded {size} bytes, latest_record_date={row[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
