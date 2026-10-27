# Configuración común del recorrido Colima/Kubernetes. Compatible con bash y zsh.
# El script llamante define PROJECT_DIR antes de cargar este archivo.
APP_NAMESPACE="trendo-demo"
FS_NAMESPACE="visionone-filesecurity"
FS_RELEASE="my-release"
FS_CHART_VERSION="1.6.3"
KUBE_CONTEXT="colima"
BACKEND_REMOTE_PORT="8007"
FRONTEND_REMOTE_PORT="80"
BACKEND_LOCAL_PORT="9000"
FRONTEND_LOCAL_PORT="8081"
ENV_FILE="$PROJECT_DIR/.env.demo.local"
RUNTIME_DIR="$PROJECT_DIR/.runtime"
SECRET_DIR="$RUNTIME_DIR/secrets"
LOG_DIR="$RUNTIME_DIR/logs"
SECRET_RENDERED="$SECRET_DIR/application.json"
FS_SECRET_FILE="$SECRET_DIR/file-security.json"
BACKEND_PF_LOG="$LOG_DIR/backend-portforward.log"
FRONTEND_PF_LOG="$LOG_DIR/frontend-portforward.log"
FS_VALUES_FILE="$PROJECT_DIR/k8s/file-security.values.yaml"

load_demo_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: falta $ENV_FILE. Copia .env.demo.local.example y completa los valores."
    return 1
  fi
  set -a
  source "$ENV_FILE"
  set +a
}

kubectl() {
  command kubectl --context "$KUBE_CONTEXT" "$@"
}

helm() {
  command helm --kube-context "$KUBE_CONTEXT" "$@"
}

stop_demo_ports() {
  python3 "$PROJECT_DIR/scripts/lib/port-forwards.py" stop "$RUNTIME_DIR" "$KUBE_CONTEXT" "$APP_NAMESPACE" "$BACKEND_LOCAL_PORT" "$FRONTEND_LOCAL_PORT"
}

start_demo_ports() {
  python3 "$PROJECT_DIR/scripts/lib/port-forwards.py" start "$RUNTIME_DIR" "$KUBE_CONTEXT" "$APP_NAMESPACE" "$BACKEND_LOCAL_PORT" "$FRONTEND_LOCAL_PORT"
}
