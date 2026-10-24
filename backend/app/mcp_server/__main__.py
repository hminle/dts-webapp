"""Run the MCP server over stdio: ``uv run python -m app.mcp_server``."""

from app.main import app
from app.mcp_server.server import build_server


def main() -> None:
    build_server(app).run(show_banner=False)


if __name__ == "__main__":
    main()
