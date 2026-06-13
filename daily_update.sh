#!/bin/bash
# Daily wiki update — run via crontab
# Example: 30 8 * * * /Users/archersado/workspace/deep-wiki/daily_update.sh >> /Users/archersado/workspace/deep-wiki/daily_update.log 2>&1

set -euo pipefail

PROJECT_DIR="/Users/archersado/workspace/deep-wiki"
PYTHON="$PROJECT_DIR/.venv/bin/python"

cd "$PROJECT_DIR"
"$PYTHON" run_daily.py
