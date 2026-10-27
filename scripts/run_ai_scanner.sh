#!/bin/bash
# Evaluación directa del modelo. --check solo valida el esquema, sin credenciales ni scan.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/security/ai-scanner/tmas-aiscan-llm-config.yaml"
CHECK_ONLY=false
case "${1:-}" in
  --check) CHECK_ONLY=true ;;
  "") ;;
  *) echo "Uso: $0 [--check]" >&2; exit 1 ;;
esac
if [[ $# -gt 1 ]]; then echo "Uso: $0 [--check]" >&2; exit 1; fi

# Este preflight no lee ni exporta las credenciales locales.
if ! $CHECK_ONLY; then
  existing_target="${TARGET_API_KEY:-${OPENAI_API_KEY:-}}"
  existing_tmas="${TMAS_API_KEY:-}"
  if [[ -f "$PROJECT_ROOT/.env.demo.local" ]]; then
    set -a
    source "$PROJECT_ROOT/.env.demo.local"
    set +a
  fi
  export TARGET_API_KEY="${existing_target:-${OPENAI_API_KEY:-}}"
  export TMAS_API_KEY="${existing_tmas:-${TMAS_API_KEY:-}}"
  for variable in TMAS_API_KEY TARGET_API_KEY; do
    value="${!variable:-}"
    if [[ -z "$value" || "$value" == "RELLENAR" ]]; then
      if [[ "$variable" == "TARGET_API_KEY" ]]; then
        echo "ERROR: falta OPENAI_API_KEY (o TARGET_API_KEY). En GitHub añade el secreto OPENAI_API_KEY en Settings > Secrets and variables > Actions." >&2
      else
        echo "ERROR: falta TMAS_API_KEY. Configura la clave local o el secreto de Actions correspondiente." >&2
      fi
      exit 1
    fi
  done
fi

TMAS_BINARY="$(python3 "$SCRIPT_DIR/lib/install-tmas.py")"
"$TMAS_BINARY" --env-file /dev/null aiscan llm config validate "$CONFIG_FILE"
if $CHECK_ONLY; then
  echo "Configuración de AI Scanner válida. No se ha iniciado ningún escaneo."
  exit 0
fi

# Carpeta nueva por ejecución: no se confunden informes antiguos con un scan fallido.
RESULTS_ROOT="${AI_SCAN_RESULTS_DIR:-$PROJECT_ROOT/.runtime/ai-scanner/results}"
mkdir -p "$RESULTS_ROOT"
RESULTS_DIR="$(mktemp -d "$RESULTS_ROOT/scan-XXXXXXXX")"
echo "Iniciando evaluación del modelo. Resultados: $RESULTS_DIR"
(
  cd "$RESULTS_DIR"
  "$TMAS_BINARY" --env-file /dev/null aiscan llm --config "$CONFIG_FILE" --region eu-central-1 --yes
)
echo "Escaneo completado. Informes JSON y Markdown en $RESULTS_DIR"
