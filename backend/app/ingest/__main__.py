"""Command line: ``uv run --group ingest python -m app.ingest --db PATH [--full]``.

Exit codes: 0 success (changed or not), 1 fetch or validation failure, 2 usage
error. When ``GITHUB_OUTPUT`` is set, ``changed`` and ``latest_record_date`` are
written there for later workflow steps.
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.config import get_settings
from app.ingest.build import MissingArtifact, build
from app.ingest.treasury_client import TreasuryAPIError
from app.ingest.validate import ArtifactInvalid

logger = logging.getLogger("app.ingest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingest")
    parser.add_argument("--db", type=Path, required=True, help="artifact path")
    parser.add_argument("--full", action="store_true", help="rebuild from 2005")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="upper bound for record_date (YYYY-MM-DD), default today in UTC",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    try:
        result = build(
            args.db, full=args.full, today=args.today, settings=get_settings()
        )
    except MissingArtifact as exc:
        logger.error("%s", exc)
        return 2
    except (TreasuryAPIError, ArtifactInvalid) as exc:
        logger.error("ingest failed, artifact left unchanged: %s", exc)
        return 1

    print(json.dumps(asdict(result)))
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"changed={'true' if result.changed else 'false'}\n")
            f.write(f"latest_record_date={result.latest_record_date or ''}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
