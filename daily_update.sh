#!/bin/bash
# Daily wiki update — run via crontab

set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
exec "$HOME/.local/bin/poetry" run python run_daily.py
