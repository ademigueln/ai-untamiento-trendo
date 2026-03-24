#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

APP_NAMESPACE="trendo-demo"
FS_NAMESPACE="visionone-filesecurity"
FS_RELEASE="my-release"

BACKEND_LOCAL_PORT="9000"
BACKEND_REMOTE_PORT="8007"

FRONTEND_LOCAL_PORT="8081"
FRONTEND_REMOTE_PORT="80"

BACKEND_PF_LOG="$PROJECT_DIR/backend-portforward.log"
FRONTEND_PF_LOG="$PROJECT_DIR/frontend-portforward.log"

echo "==============================================="
echo " AI-untamiento de Trendo - Despliegue completo "
echo "==============================================="
echo ""

cd "$PROJECT_DIR"

# --------------------------------------------------
# 1. Docker
# --------------------------------------------------
echo "[1/11] Comprobando Docker Desktop..."

if ! docker info >/dev/null 2>&1; then
  echo "Docker no está listo. Intentando abrir Docker Desktop..."
  open -a Docker >/dev/null 2>&1 || true

  echo "Esperando a que Docker arranque..."
  for i in {1..60}; do
    if docker info >/dev/null 2>&1; then
      break
    fi
    sleep 5
  done
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker Desktop no responde."
  exit 1
fi

echo "Docker OK"
echo ""

# --------------------------------------------------
# 2. Kubernetes
# --------------------------------------------------
echo "[2/11] Comprobando Kubernetes..."

for i in {1..60}; do
  if kubectl cluster-info >/dev/null 2>&1; then
    break
  fi
  echo "Esperando a Kubernetes..."
  sleep 5
done

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "ERROR: Kubernetes no responde."
  exit 1
fi

echo "Kubernetes OK"
echo ""

# --------------------------------------------------
# 3. Namespaces
# --------------------------------------------------
echo "[3/11] Asegurando namespaces..."
kubectl create namespace "$APP_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$FS_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
echo "Namespaces OK"
echo ""

# --------------------------------------------------
# 4. Secrets demo app
# --------------------------------------------------
echo "[4/11] Aplicando secrets de la demo..."
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/file-security-secrets.yaml
echo "Secrets OK"
echo ""

# --------------------------------------------------
# 5. Instalar/actualizar File Security
# --------------------------------------------------
echo "[5/11] Instalando/actualizando Trend File Security..."
helm repo add visionone-filesecurity https://trendmicro.github.io/visionone-file-security-helm/ >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1

helm upgrade --install "$FS_RELEASE" visionone-filesecurity/visionone-filesecurity \
  -n "$FS_NAMESPACE"

echo "Esperando a File Security..."
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-management-service -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scan-cache -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scanner -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-backend-communicator -n "$FS_NAMESPACE" --timeout=300s || true

echo "Estado actual File Security:"
kubectl get pods -n "$FS_NAMESPACE"
echo ""

# --------------------------------------------------
# 6. Aplicar manifiestos demo
# --------------------------------------------------
echo "[6/11] Aplicando manifiestos Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

if [ -f "k8s/ingress.yaml" ]; then
  kubectl apply -f k8s/ingress.yaml || true
fi

echo "Manifiestos OK"
echo ""

# --------------------------------------------------
# 7. Reiniciar app
# --------------------------------------------------
echo "[7/11] Reiniciando backend y frontend..."
kubectl rollout restart deployment/backend -n "$APP_NAMESPACE"
kubectl rollout restart deployment/frontend -n "$APP_NAMESPACE"

kubectl rollout status deployment/backend -n "$APP_NAMESPACE" --timeout=300s
kubectl rollout status deployment/frontend -n "$APP_NAMESPACE" --timeout=300s

echo "Backend y frontend OK"
echo ""

# --------------------------------------------------
# 8. DNS interno scanner
# --------------------------------------------------
echo "[8/11] Verificando DNS del scanner..."
kubectl exec -n "$APP_NAMESPACE" deployment/backend -- python - <<'PY'
import socket
host = "my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local"
print(socket.gethostbyname(host))
PY

echo "DNS scanner OK"
echo ""

# --------------------------------------------------
# 9. Reiniciar port-forwards
# --------------------------------------------------
echo "[9/11] Reiniciando port-forwards..."
pkill -f "port-forward -n $APP_NAMESPACE service/backend-service" 2>/dev/null || true
pkill -f "port-forward -n $APP_NAMESPACE service/frontend-service" 2>/dev/null || true

rm -f "$BACKEND_PF_LOG" "$FRONTEND_PF_LOG"

nohup kubectl port-forward -n "$APP_NAMESPACE" service/backend-service "${BACKEND_LOCAL_PORT}:${BACKEND_REMOTE_PORT}" > "$BACKEND_PF_LOG" 2>&1 &
sleep 2

nohup kubectl port-forward -n "$APP_NAMESPACE" service/frontend-service "${FRONTEND_LOCAL_PORT}:${FRONTEND_REMOTE_PORT}" > "$FRONTEND_PF_LOG" 2>&1 &
sleep 2

echo "Port-forwards OK"
echo ""

# --------------------------------------------------
# 10. Estado final
# --------------------------------------------------
echo "[10/11] Estado final"
echo ""
echo "Pods app:"
kubectl get pods -n "$APP_NAMESPACE"
echo ""
echo "Pods file security:"
kubectl get pods -n "$FS_NAMESPACE"
echo ""

# --------------------------------------------------
# 11. URLs
# --------------------------------------------------
echo "[11/11] URLs"
echo ""
echo "Frontend: http://127.0.0.1:${FRONTEND_LOCAL_PORT}"
echo "Backend:  http://127.0.0.1:${BACKEND_LOCAL_PORT}"
echo ""
echo "Logs port-forward backend:  $BACKEND_PF_LOG"
echo "Logs port-forward frontend: $FRONTEND_PF_LOG"
echo ""
echo "Despliegue completo OK"
