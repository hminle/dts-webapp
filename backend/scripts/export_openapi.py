"""Export the FastAPI OpenAPI spec to ``docs/contracts/openapi.json``.

The committed snapshot is the API contract the frontend generates its typed
client from (``pnpm gen:api``). Regenerate it in the same commit as any
endpoint change:

    uv run python -m scripts.export_openapi
"""

import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "contracts" / "openapi.json"
)


def main() -> None:
    spec = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUTPUT_PATH} ({len(spec.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
