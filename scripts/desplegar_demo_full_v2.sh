#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

source "$SCRIPT_DIR/lib/demo-config.sh"

CHECK_ONLY=false
REPAIR_SECURITY=false
for argument in "$@"; do
  case "$argument" in
    --check) CHECK_ONLY=true ;;
    --repair-security) REPAIR_SECURITY=true ;;
    *) echo "Uso: $0 [--check] [--repair-security]"; exit 1 ;;
  esac
done

echo "="
echo " AI-untamiento de Trendo - Despliegue completo "
echo "="
echo ""

# 1. Validaciones de ficheros locales
echo "[1/13] Validando ficheros de configuración..."
load_demo_env

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
# Validar valores antes de arrancar Colima o modificar Kubernetes.
for var_name in OPENAI_API_KEY TREND_API_KEY FILE_SECURITY_API_KEY FILE_SECURITY_REGISTRATION_TOKEN; do
  value="${(P)var_name}"
  if [[ "$value" == "RELLENAR" || "$value" == *"TU_"* || "$value" == *"tu_"* ]]; then
    echo "ERROR: completa $var_name en .env.demo.local"
    exit 1
  fi
done
for port in "$BACKEND_LOCAL_PORT" "$FRONTEND_LOCAL_PORT"; do
  if [[ "$port" != <-> ]] || (( port < 1 || port > 65535 )); then
    echo "ERROR: los puertos locales deben estar entre 1 y 65535"
    exit 1
  fi
done
if [[ "$BACKEND_LOCAL_PORT" == "$FRONTEND_LOCAL_PORT" ]]; then
  echo "ERROR: backend y frontend deben usar puertos locales distintos"
  exit 1
fi
for dependency in colima docker kubectl helm curl python3; do
  if ! whence -p "$dependency" >/dev/null 2>&1; then
    echo "ERROR: '$dependency' no está instalado o no está en PATH."
    exit 1
  fi
done
for manifest in namespace.yaml pvc.yaml backend.yaml frontend.yaml config.yaml file-security.values.yaml; do
  if [[ ! -f "$PROJECT_DIR/k8s/$manifest" ]]; then
    echo "ERROR: falta k8s/$manifest"
    exit 1
  fi
done
if [[ ! -f "$SCRIPT_DIR/lib/render-secrets.py" || ! -f "$SCRIPT_DIR/lib/port-forwards.py" || ! -f "$SCRIPT_DIR/lib/build-images.py" ]]; then
  echo "ERROR: falta un helper de scripts/lib/"
  exit 1
fi
echo "Configuración y dependencias locales OK"
if $CHECK_ONLY; then
  echo "Comprobación completada. No se ha iniciado ni modificado el clúster."
  exit 0
fi
umask 077
mkdir -p "$SECRET_DIR" "$LOG_DIR"

echo "[2/13] Comprobando runtime de Colima/Docker..."
if ! colima status >/dev/null 2>&1; then
  echo "Colima no está iniciado. Arrancando con 4 CPUs, 8 GB RAM y Kubernetes..."
  colima start --cpus 4 --memory 8 --runtime docker --kubernetes
fi

# Exportar socket de Docker de Colima por si no está en el entorno.
export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
unset DOCKER_CONTEXT
if ! docker info >/dev/null 2>&1; then
  echo "Esperando a que el demonio de Docker de Colima esté listo..."
  for i in {1..30}; do
    if docker info >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: El demonio de Docker en Colima no responde."
  exit 1
fi
echo "Docker / Colima OK"
echo ""

# 3. Kubernetes
echo "[3/13] Comprobando Kubernetes..."
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "Iniciando Kubernetes en Colima..."
  colima kubernetes start
fi
for i in {1..60}; do
  if kubectl cluster-info >/dev/null 2>&1; then
    break
  fi
  echo "Esperando a que el cluster de Kubernetes esté listo..."
  sleep 5
done
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "ERROR: Kubernetes no responde."
  exit 1
fi
echo "Kubernetes OK"
echo ""

# 4. Namespaces
echo "[4/13] Asegurando namespaces..."
kubectl create namespace "$APP_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$FS_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
echo "Namespaces OK"
echo ""

# 5-6. Generar secretos fuera de los manifiestos versionados.
echo "[5/13] Preparando secretos de aplicación..."
echo "[6/13] Conservando el registro existente de File Security..."
# Un fallo de consulta debe abortar; no equivale a un token ausente.
device_secret=$(kubectl get secret device-token-secret -n "$FS_NAMESPACE" --ignore-not-found -o name)
initialize_device="no"
[[ -n "$device_secret" ]] || initialize_device="yes"
python3 "$SCRIPT_DIR/lib/render-secrets.py" "$SECRET_DIR" "$APP_NAMESPACE" "$FS_NAMESPACE" "$initialize_device"

# 7. Aplicar secrets de aplicación y File Security
echo "[7/13] Aplicando secrets..."
kubectl apply -f "$SECRET_RENDERED"
kubectl apply -f "$FS_SECRET_FILE"
echo "Secrets aplicados"
echo ""

# 8. Instalar/actualizar File Security
echo "[8/13] Instalando/actualizando Trend File Security..."
helm repo add visionone-filesecurity https://trendmicro.github.io/visionone-file-security-helm/ --force-update >/dev/null
helm repo update >/dev/null 2>&1
# Obtener la IP del API Server o usar la subred de Docker/Colima.
K8S_API_IP=$(kubectl get endpoints kubernetes -n default -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || true)
K8S_API_IP="${K8S_API_IP:-172.18.0.0/16}"
helm upgrade --install "$FS_RELEASE" visionone-filesecurity/visionone-filesecurity -n "$FS_NAMESPACE" \
  --set "visiononeFilesecurity.noProxy=localhost\\,127.0.0.1\\,.cluster.local\\,.svc.cluster.local\\,${K8S_API_IP}\\,172.18.0.0/16" \
  --values "$FS_VALUES_FILE" --version "$FS_CHART_VERSION"

echo "Esperando a componentes de File Security..."
# El registro debe completarse antes de que pueda arrancar la gestión.
if $REPAIR_SECURITY; then
  kubectl rollout restart deployment/"$FS_RELEASE"-visionone-filesecurity-backend-communicator -n "$FS_NAMESPACE"
fi
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-backend-communicator -n "$FS_NAMESPACE" --timeout=300s
if $REPAIR_SECURITY; then
  kubectl rollout restart deployment/"$FS_RELEASE"-visionone-filesecurity-management-service -n "$FS_NAMESPACE"
fi
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-management-service -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scan-cache -n "$FS_NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$FS_RELEASE"-visionone-filesecurity-scanner -n "$FS_NAMESPACE" --timeout=300s
echo "File Security OK"
echo ""

# 9. Aplicar manifiestos de la demo
echo "[9/13] Preparando imágenes del código local y aplicando manifiestos..."
python3 "$SCRIPT_DIR/lib/build-images.py" "$PROJECT_DIR"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/config.yaml
kubectl apply -f "$RUNTIME_DIR/manifests/backend.yaml"
kubectl apply -f "$RUNTIME_DIR/manifests/frontend.yaml"
if [ -f "k8s/ingress.yaml" ]; then
  if ! kubectl apply -f k8s/ingress.yaml; then
    echo "Ingress no aplicado; el acceso local seguirá usando port-forward."
  fi
fi
echo "Manifiestos OK"
echo ""

# 10. Recoger credenciales y esperar a las aplicaciones
echo "[10/13] Actualizando backend y esperando a las aplicaciones..."
kubectl rollout restart deployment/backend -n "$APP_NAMESPACE"
kubectl rollout status deployment/backend -n "$APP_NAMESPACE" --timeout=300s
kubectl rollout status deployment/frontend -n "$APP_NAMESPACE" --timeout=300s
echo "Backend y frontend OK"
echo ""

# 11. Verificar DNS interno del scanner
echo "[11/13] Verificando DNS interno del scanner..."
kubectl exec -i -n "$APP_NAMESPACE" deployment/backend -- python - <<'PY'
import os
import socket
host = os.environ["FILE_SECURITY_HOST"].rsplit(":", 1)[0]
print(socket.gethostbyname(host))
PY
echo "DNS scanner OK"
echo ""

# 12. Reiniciar port-forwards
echo "[12/13] Reiniciando port-forwards..."
start_demo_ports
echo "Port-forwards iniciados"
echo ""

echo "[CHECK] Comprobando acceso HTTP a backend y frontend..."
for url in "http://127.0.0.1:${BACKEND_LOCAL_PORT}/" "http://127.0.0.1:${BACKEND_LOCAL_PORT}/api/stats" "http://127.0.0.1:${FRONTEND_LOCAL_PORT}/" "http://127.0.0.1:${FRONTEND_LOCAL_PORT}/api/stats"; do
  if ! curl --fail --silent --show-error --retry 5 --retry-connrefused --retry-delay 1 --connect-timeout 2 --max-time 10 "$url" >/dev/null; then
    echo "ERROR: no responde $url. Revisa los logs en $LOG_DIR"
    exit 1
  fi
done
echo "[OK] Portal accesible. Usa los diagnósticos para probar AI Guard y File Security."

# 13. Estado final
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
