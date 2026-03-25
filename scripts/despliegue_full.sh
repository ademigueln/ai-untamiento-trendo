# scripts/desplegar_demo_full.sh
#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

APP_NAMESPACE="trendo-demo"
FS_NAMESPACE="visionone-filesecurity"
FS_RELEASE="my-release"

BACKEND_REMOTE_PORT="8007"
FRONTEND_REMOTE_PORT="80"

ENV_FILE=".env.demo.local"
SECRET_TEMPLATE="k8s/secret.yaml.template"
SECRET_RENDERED="k8s/secret.yaml"
FS_SECRET_FILE="k8s/file-security-secrets.yaml"

BACKEND_PF_LOG="$PROJECT_DIR/backend-portforward.log"
FRONTEND_PF_LOG="$PROJECT_DIR/frontend-portforward.log"

echo "==============================================="
echo " AI-untamiento de Trendo - Despliegue completo "
echo "==============================================="
echo ""

# --------------------------------------------------
# 1. Validaciones de ficheros locales
# --------------------------------------------------
echo "[1/13] Validando ficheros de configuración..."

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: falta $ENV_FILE"
  echo "Crea una copia desde el ejemplo:"
  echo "  cp .env.demo.local.example .env.demo.local"
  exit 1
fi

if [ ! -f "$SECRET_TEMPLATE" ]; then
  echo "ERROR: falta $SECRET_TEMPLATE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

required_vars=(
  OPENAI_API_KEY
  TREND_API_KEY
  FILE_SECURITY_API_KEY
  FILE_SECURITY_REGISTRATION_TOKEN
  TREND_AI_URL
  TREND_AI_APP_NAME
  FILE_SECURITY_HOST
  BACKEND_LOCAL_PORT
  FRONTEND_LOCAL_PORT
)

for var_name in "${required_vars[@]}"; do
  if [ -z "${(P)var_name:-}" ]; then
    echo "ERROR: falta la variable $var_name en $ENV_FILE"
    exit 1
  fi
done

echo "Configuración local OK"
echo ""

# --------------------------------------------------
# 2. Docker
# --------------------------------------------------
echo "[2/13] Comprobando Docker Desktop..."

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
# 3. Kubernetes
# --------------------------------------------------
echo "[3/13] Comprobando Kubernetes..."

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
# 4. Namespaces
# --------------------------------------------------
echo "[4/13] Asegurando namespaces..."
kubectl create namespace "$APP_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$FS_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
echo "Namespaces OK"
echo ""

# --------------------------------------------------
# 5. Renderizar secret.yaml localmente desde plantilla
# --------------------------------------------------
echo "[5/13] Generando secret.yaml local desde plantilla..."
cp "$SECRET_TEMPLATE" "$SECRET_RENDERED"

sed -i.bak "s|__OPENAI_API_KEY__|$OPENAI_API_KEY|g" "$SECRET_RENDERED"
sed -i.bak "s|__TREND_API_KEY__|$TREND_API_KEY|g" "$SECRET_RENDERED"
sed -i.bak "s|__FILE_SECURITY_API_KEY__|$FILE_SECURITY_API_KEY|g" "$SECRET_RENDERED"
sed -i.bak "s|__FILE_SECURITY_HOST__|$FILE_SECURITY_HOST|g" "$SECRET_RENDERED"
rm -f "${SECRET_RENDERED}.bak"

echo "secret.yaml generado"
echo ""

# --------------------------------------------------
# 6. Generar secret de File Security localmente
# --------------------------------------------------
echo "[6/13] Generando file-security-secrets.yaml localmente..."
cat > "$FS_SECRET_FILE" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: token-secret
  namespace: $FS_NAMESPACE
type: Opaque
stringData:
  registration-token: "$FILE_SECURITY_REGISTRATION_TOKEN"

---
apiVersion: v1
kind: Secret
metadata:
  name: device-token-secret
  namespace: $FS_NAMESPACE
type: Opaque
stringData: {}
EOF

echo "file-security-secrets.yaml generado"
echo ""

# --------------------------------------------------
# 7. Aplicar secrets de aplicación y File Security
# --------------------------------------------------
echo "[7/13] Aplicando secrets..."
kubectl apply -f "$SECRET_RENDERED"
kubectl apply -f "$FS_SECRET_FILE"
echo "Secrets aplicados"
echo ""

# --------------------------------------------------
# 8. Instalar/actualizar File Security
# --------------------------------------------------
echo "[8/13] Instalando/actualizando Trend File Security..."
helm repo add visionone-filesecurity https://trendmicro.github.io/visionone-file-security-helm/ >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1

helm upgrade --install "$FS_RELEASE" visionone-filesecurity/visionone-filesecurity \
  -n "$FS_NAMESPACE"

echo "Esperando a componentes de File Security..."
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-management-service -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scan-cache -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scanner -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-backend-communicator -n "$FS_NAMESPACE" --timeout=300s

echo "File Security OK"
echo ""

# --------------------------------------------------
# 9. Aplicar manifiestos de la demo
# --------------------------------------------------
echo "[9/13] Aplicando manifiestos Kubernetes..."
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
# 10. Reiniciar backend y frontend
# --------------------------------------------------
echo "[10/13] Reiniciando backend y frontend..."
kubectl rollout restart deployment/backend -n "$APP_NAMESPACE"
kubectl rollout restart deployment/frontend -n "$APP_NAMESPACE"

kubectl rollout status deployment/backend -n "$APP_NAMESPACE" --timeout=300s
kubectl rollout status deployment/frontend -n "$APP_NAMESPACE" --timeout=300s

echo "Backend y frontend OK"
echo ""

# --------------------------------------------------
# 11. Verificar DNS interno del scanner
# --------------------------------------------------
echo "[11/13] Verificando DNS interno del scanner..."
kubectl exec -n "$APP_NAMESPACE" deployment/backend -- python - <<'PY'
import socket
host = "my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local"
print(socket.gethostbyname(host))
PY

echo "DNS scanner OK"
echo ""

# --------------------------------------------------
# 12. Reiniciar port-forwards
# --------------------------------------------------
echo "[12/13] Reiniciando port-forwards..."
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
# 13. Estado final
# --------------------------------------------------
echo "[13/13] Estado final"
echo ""
echo "Pods app:"
kubectl get pods -n "$APP_NAMESPACE"
echo ""
echo "Pods file security:"
kubectl get pods -n "$FS_NAMESPACE"
echo ""
echo "Frontend: http://127.0.0.1:${FRONTEND_LOCAL_PORT}"
echo "Backend:  http://127.0.0.1:${BACKEND_LOCAL_PORT}"
echo ""
echo "Logs port-forward backend:  $BACKEND_PF_LOG"
echo "Logs port-forward frontend: $FRONTEND_PF_LOG"
echo ""
echo "Despliegue completo OK"