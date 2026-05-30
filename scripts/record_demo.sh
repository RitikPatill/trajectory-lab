#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v asciinema >/dev/null 2>&1 || { echo "asciinema not found: https://asciinema.org/"; exit 1; }

export TLAB_DB="${TLAB_DB:-$HOME/.tlab/demo.db}"
mkdir -p "$(dirname "$TLAB_DB")"
mkdir -p "$REPO_ROOT/docs"

echo "Recording CLI demo..."
asciinema rec "$REPO_ROOT/docs/demo.cast" \
    --command "bash $REPO_ROOT/scripts/_demo_commands.sh" \
    --title "TrajectoryLab CLI demo" \
    --overwrite

if command -v agg >/dev/null 2>&1; then
    echo "Converting to GIF with agg..."
    agg "$REPO_ROOT/docs/demo.cast" "$REPO_ROOT/docs/demo.gif"
    echo "Saved: docs/demo.gif"
else
    echo "agg not found. To convert: https://github.com/asciinema/agg"
    echo "  agg docs/demo.cast docs/demo.gif"
fi
