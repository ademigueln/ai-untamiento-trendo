#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/lib/demo-config.sh"
load_demo_env
export UPLOAD_DIR="$PROJECT_DIR/.runtime/dev/uploads"
export EVENTS_DB="$PROJECT_DIR/.runtime/dev/events.sqlite3"
cd "$PROJECT_DIR/portal-backend"
PYTHON="$PROJECT_DIR/.runtime/test-venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Crea primero un entorno Python 3.11 e instala portal-backend/requirements.lock; consulta docs/development.md."
  exit 1
fi
exec "$PYTHON" -m uvicorn main:app --host 127.0.0.1 --port 8007 --reload --no-access-log
