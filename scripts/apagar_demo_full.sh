#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

APP_NAMESPACE="trendo-demo"
FS_NAMESPACE="visionone-filesecurity"
FS_RELEASE="my-release"

echo "==============================================="
echo " AI-untamiento de Trendo - Apagado total demo "
echo "==============================================="
echo ""

cd "$PROJECT_DIR"

# --------------------------------------------------
# 1. Matar port-forwards
# --------------------------------------------------
echo "[1/6] Matando port-forwards..."
pkill -f "port-forward -n $APP_NAMESPACE service/backend-service" 2>/dev/null || true
pkill -f "port-forward -n $APP_NAMESPACE service/frontend-service" 2>/dev/null || true
echo "Port-forwards detenidos"
echo ""

# --------------------------------------------------
# 2. Desinstalar File Security Helm release
# --------------------------------------------------
echo "[2/6] Desinstalando File Security release..."
helm uninstall "$FS_RELEASE" -n "$FS_NAMESPACE" >/dev/null 2>&1 || true
echo "Release de File Security eliminada (si existía)"
echo ""

# --------------------------------------------------
# 3. Borrar namespace de aplicación
# --------------------------------------------------
echo "[3/6] Borrando namespace de aplicación..."
kubectl delete namespace "$APP_NAMESPACE" --ignore-not-found=true
echo "Namespace $APP_NAMESPACE borrado (o ya no existía)"
echo ""

# --------------------------------------------------
# 4. Borrar namespace de File Security
# --------------------------------------------------
echo "[4/6] Borrando namespace de File Security..."
kubectl delete namespace "$FS_NAMESPACE" --ignore-not-found=true
echo "Namespace $FS_NAMESPACE borrado (o ya no existía)"
echo ""

# --------------------------------------------------
# 5. Esperar a que desaparezcan namespaces
# --------------------------------------------------
echo "[5/6] Esperando a que desaparezcan los namespaces..."

for ns in "$APP_NAMESPACE" "$FS_NAMESPACE"; do
  for i in {1..60}; do
    if ! kubectl get namespace "$ns" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
done

echo "Namespaces eliminados o no presentes"
echo ""

# --------------------------------------------------
# 6. Limpieza local de logs
# --------------------------------------------------
echo "[6/6] Limpiando logs locales..."
rm -f "$PROJECT_DIR/backend-portforward.log"
rm -f "$PROJECT_DIR/frontend-portforward.log"
echo "Logs locales eliminados"
echo ""

echo "Apagado completo de la demo finalizado."
echo ""
echo "Ahora puedes probar arranque desde cero con:"
echo "  ./scripts/desplegar_demo_full.sh"
