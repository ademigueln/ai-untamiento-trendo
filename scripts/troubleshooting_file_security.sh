#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/lib/demo-config.sh"
load_demo_env || exit 1
NAMESPACE="$APP_NAMESPACE"
mkdir -p "$LOG_DIR"

TMP_FILE="/tmp/eicar.txt"

start_demo_ports || exit 1

echo "Probando File Security..."
curl -s -X POST "http://127.0.0.1:${BACKEND_LOCAL_PORT}/api/files/upload" \
  -F "file=@${TMP_FILE}"

echo ""
echo ""
echo "Logs backend:"
kubectl logs deployment/backend -n "$NAMESPACE" --tail=120
