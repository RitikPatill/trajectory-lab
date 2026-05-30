#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
echo "=== TrajectoryLab Demo ==="
echo ""
echo "$ uv run python scripts/seed_demo.py"
uv run python scripts/seed_demo.py
echo ""
echo "$ uv run tlab compare 1 2"
uv run tlab compare 1 2
echo ""
echo "Dashboard: http://localhost:3000"
echo "Press Ctrl-C to exit."
