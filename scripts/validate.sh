#!/bin/zsh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"
PYTHON="$PROJECT_DIR/.runtime/test-venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Prepara el entorno Python siguiendo docs/development.md."
  exit 1
fi
(cd portal-backend && "$PYTHON" -m unittest discover -s tests -v)
python3 -m unittest discover -s scripts/tests -v
npm run format:check --prefix portal-frontend
npm run lint --prefix portal-frontend -- --max-warnings 0
npm run build --prefix portal-frontend
