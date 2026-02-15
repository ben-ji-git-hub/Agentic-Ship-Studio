#!/usr/bin/env bash
set -euo pipefail

DEMO_REPO="${1:-./demo-repo-video}"
PORT="${2:-8765}"
MODE="${3:---fresh}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$DEMO_REPO" != /* ]]; then
  DEMO_REPO="${ROOT_DIR}/${DEMO_REPO#./}"
fi

if [ "$MODE" != "--fresh" ] && [ "$MODE" != "--no-fresh" ]; then
  echo "Usage: ./scripts/run_video_demo.sh [demo_repo_dir] [port] [--fresh|--no-fresh]"
  exit 2
fi

if [ "$MODE" = "--fresh" ]; then
  "$ROOT_DIR/scripts/create_video_demo_repo.sh" "$DEMO_REPO" --force
elif [ ! -d "$DEMO_REPO" ]; then
  "$ROOT_DIR/scripts/create_video_demo_repo.sh" "$DEMO_REPO"
fi

echo "Running baseline audit for demo scoreboard..."
python3 -m vibe_sentinel audit "$DEMO_REPO" --output-dir "$DEMO_REPO/.vibe-sentinel"
echo ""
echo "Starting Vibe Sentinel Studio on http://127.0.0.1:${PORT}"
echo "Use this demo repo path in Studio: $(cd "$DEMO_REPO" && pwd)"
python3 -m vibe_sentinel studio --host 127.0.0.1 --port "$PORT"
