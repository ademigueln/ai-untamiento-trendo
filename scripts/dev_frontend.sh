#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../portal-frontend"
exec npm run dev -- --host 127.0.0.1
