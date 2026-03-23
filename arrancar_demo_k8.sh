#!/bin/zsh

set -e

PROJECT_DIR="/Users/alvaro_demiguel/Downloads/AI/atencion ciudadana"
NAMESPACE="trendo-demo"

BACKEND_PORT_LOCAL="9000"
BACKEND_PORT_REMOTE="8007"

FRONTEND_PORT_LOCAL="8081"
FRONTEND_PORT_REMOTE="80"

BACKEND_LOG="$PROJECT_DIR/backend-portforward.log"
FRONTEND_LOG="$PROJECT_DIR/frontend-portforward.log"

echo "=========================================="
echo " AI-untamiento de Trendo - Arranque demo "
echo "=========================================="
echo ""

cd "$PROJECT_DIR"

echo "[1/8] Comprobando Docker Desktop..."

if ! docker info >/dev/null 2>&1; then
  echo "Docker no está listo. Intentando abrir Docker Desktop..."
  open -a Docker

  echo "Esperando a que Docker arranque..."
  for i in {1..60}; do
    if docker info >/dev/null 2>&1; then
      echo "Docker OK"
      break
    fi
    sleep 5
  done
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker Desktop no ha arrancado."
  echo "Abre Docker Desktop manualmente y vuelve a ejecutar el script."
  exit 1
fi

echo ""
echo "[2/8] Comprobando Kubernetes..."
for i in {1..60}; do
  if kubectl version --client >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
    echo "Kubernetes OK"
    break
  fi
  echo "Esperando a Kubernetes..."
  sleep 5
done

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "ERROR: Kubernetes no responde."
  echo "Comprueba que Kubernetes está activado en Docker Desktop."
  exit 1
fi

echo ""
echo "[3/8] Aplicando manifiestos Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

if [ -f "k8s/ingress.yaml" ]; then
  kubectl apply -f k8s/ingress.yaml || true
fi

echo ""
echo "[4/8] Reiniciando despliegues..."
kubectl rollout restart deployment/backend -n "$NAMESPACE"
kubectl rollout restart deployment/frontend -n "$NAMESPACE"

echo ""
echo "[5/8] Esperando a que backend y frontend estén listos..."
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=180s
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=180s

echo ""
echo "[6/8] Matando port-forwards antiguos si existen..."
pkill -f "port-forward -n $NAMESPACE service/backend-service" 2>/dev/null || true
pkill -f "port-forward -n $NAMESPACE service/frontend-service" 2>/dev/null || true

sleep 2

echo ""
echo "[7/8] Levantando port-forwards..."
rm -f "$BACKEND_LOG" "$FRONTEND_LOG"

nohup kubectl port-forward -n "$NAMESPACE" service/backend-service "${BACKEND_PORT_LOCAL}:${BACKEND_PORT_REMOTE}" > "$BACKEND_LOG" 2>&1 &
sleep 2

nohup kubectl port-forward -n "$NAMESPACE" service/frontend-service "${FRONTEND_PORT_LOCAL}:${FRONTEND_PORT_REMOTE}" > "$FRONTEND_LOG" 2>&1 &
sleep 2

echo ""
echo "[8/8] Estado final"
echo ""
kubectl get pods -n "$NAMESPACE"
echo ""
echo "Backend:"
echo "  http://127.0.0.1:${BACKEND_PORT_LOCAL}"
echo "Frontend:"
echo "  http://127.0.0.1:${FRONTEND_PORT_LOCAL}"
echo ""
echo "Logs port-forward backend:  $BACKEND_LOG"
echo "Logs port-forward frontend: $FRONTEND_LOG"
echo ""
echo "Demo lista."
