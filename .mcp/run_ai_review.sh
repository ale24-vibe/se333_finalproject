#!/usr/bin/env bash
# Simple wrapper to run the AI Code Review MCP tool
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/ai_code_review.py"
