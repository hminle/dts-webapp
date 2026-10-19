#!/usr/bin/env bash
# Run the FastAPI backend and the Vite frontend together, with interleaved,
# prefixed logs. Ctrl-C stops both.
set -euo pipefail
# Job control: each background job gets its own process group, so cleanup can
# kill a whole server tree (uv -> uvicorn -> reloader) with one signal.
set -m

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
INSTALL=0

usage() {
  cat <<'USAGE'
Usage: scripts/dev.sh [options]

  --install         run `uv sync` and `pnpm install` before starting
  --backend-only    start only the FastAPI server
  --frontend-only   start only the Vite server
  -h, --help        show this help

Environment:
  BACKEND_PORT      backend port (default 8000)
  FRONTEND_PORT     frontend port (default 5173)
USAGE
}

run_backend=1
run_frontend=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install) INSTALL=1 ;;
    --backend-only) run_frontend=0 ;;
    --frontend-only) run_backend=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "error: '$1' is not installed or not on PATH" >&2; exit 1; }
}
[[ $run_backend == 1 ]] && need uv
[[ $run_frontend == 1 ]] && need pnpm

port_busy() {
  # Prefer ss, fall back to lsof; if neither exists, assume free.
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$1" 2>/dev/null | grep -q LISTEN
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    return 1
  fi
}

for spec in "$run_backend:$BACKEND_PORT:backend" "$run_frontend:$FRONTEND_PORT:frontend"; do
  IFS=: read -r enabled port name <<<"$spec"
  if [[ $enabled == 1 ]] && port_busy "$port"; then
    echo "error: port $port ($name) is already in use" >&2
    exit 1
  fi
done

# Colored, prefixed log lines so the two servers stay tellable apart.
BLUE=$'\033[34m'; MAGENTA=$'\033[35m'; RESET=$'\033[0m'
[[ -t 1 ]] || { BLUE=""; MAGENTA=""; RESET=""; }

prefix() {
  local label="$1" color="$2"
  while IFS= read -r line; do
    printf '%s[%s]%s %s\n' "$color" "$label" "$RESET" "$line"
  done
}

pids=()
cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]:-}"; do
    [[ -n "$pid" ]] && kill -- "-$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

if [[ $INSTALL == 1 ]]; then
  [[ $run_backend == 1 ]] && (cd "$ROOT/backend" && uv sync)
  [[ $run_frontend == 1 ]] && (cd "$ROOT/frontend" && pnpm install)
fi

if [[ $run_backend == 1 ]]; then
  echo "starting backend  -> http://localhost:$BACKEND_PORT (docs at /docs)"
  ( cd "$ROOT/backend" && exec uv run fastapi dev --port "$BACKEND_PORT" 2>&1 | prefix backend "$BLUE" ) &
  pids+=("$!")

  # Give the frontend proxy a live target before Vite starts.
  if command -v curl >/dev/null 2>&1; then
    for _ in $(seq 1 60); do
      curl -fsS "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1 && break
      sleep 0.5
    done
  else
    sleep 3
  fi
fi

if [[ $run_frontend == 1 ]]; then
  echo "starting frontend -> http://localhost:$FRONTEND_PORT"
  ( cd "$ROOT/frontend" \
    && VITE_API_TARGET="http://localhost:$BACKEND_PORT" \
       exec pnpm dev --port "$FRONTEND_PORT" 2>&1 | prefix frontend "$MAGENTA" ) &
  pids+=("$!")
fi

# Exit as soon as either server dies, so a crashed backend doesn't leave a
# frontend talking to nothing.
wait -n
