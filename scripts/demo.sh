#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLAB_DB="${TLAB_DB:-$HOME/.tlab/demo.db}"
export TLAB_DB
mkdir -p "$(dirname "$TLAB_DB")"

# --- prereq checks ---
command -v uv >/dev/null 2>&1 || { echo "uv not found. Install from https://github.com/astral-sh/uv"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "node not found. Install from https://nodejs.org"; exit 1; }

# --- seed or live run ---
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ANTHROPIC_API_KEY detected — running live benchmarks..."
    cd "$REPO_ROOT"
    uv run tlab run --benchmark benchmarks/research --agent agents/research_v1.yaml
    uv run tlab run --benchmark benchmarks/research --agent agents/research_v2.yaml
else
    echo "No ANTHROPIC_API_KEY — seeding demo data..."
    cd "$REPO_ROOT"
    uv run python scripts/seed_demo.py
fi

# --- install web deps if needed ---
if [[ ! -d "$REPO_ROOT/web/node_modules" ]]; then
    echo "Installing web dependencies..."
    (cd "$REPO_ROOT/web" && npm install --silent)
fi

# --- start API server ---
echo "Starting API server on :8000..."
cd "$REPO_ROOT"
uv run tlab serve --port 8000 &
API_PID=$!

# --- start Next.js dev server ---
echo "Starting Next.js dev server on :3000..."
(cd "$REPO_ROOT/web" && npm run dev -- --port 3000) &
WEB_PID=$!

trap 'echo "Stopping servers..."; kill $API_PID $WEB_PID 2>/dev/null; exit 0' INT TERM EXIT

# --- wait for servers to be ready ---
echo "Waiting for API..."
for i in $(seq 1 30); do
    curl -sf http://localhost:8000/runs >/dev/null 2>&1 && break
    sleep 1
done

echo "Waiting for dashboard..."
for i in $(seq 1 60); do
    curl -sf http://localhost:3000 >/dev/null 2>&1 && break
    sleep 1
done

# --- open browser ---
URL="http://localhost:3000"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$URL"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    cmd.exe /c start "" "$URL" 2>/dev/null || true
else
    xdg-open "$URL" 2>/dev/null || true
fi

echo ""
echo "TrajectoryLab is running."
echo "  Dashboard:  http://localhost:3000"
echo "  API docs:   http://localhost:8000/docs"
echo ""
echo "Press Ctrl-C to stop."
wait
