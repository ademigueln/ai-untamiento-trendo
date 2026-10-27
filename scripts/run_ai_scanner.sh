#!/bin/bash
# -------------------------------------------------------------------
# run_ai_scanner.sh
#
# Lanza el TMAS AI Scanner contra el modelo LLM del chatbot
# (gpt-4o-mini) en modo local.
#
# Requiere:
#   - TMAS_API_KEY exportada (tu Vision One API key)
#   - OPENAI_API_KEY exportada (o definida en .env.demo.local)
#
# Uso:
#   ./scripts/run_ai_scanner.sh
#
# Los resultados se guardan en:
#   .runtime/ai-scanner/results/ai-scanner-results.json
#   .runtime/ai-scanner/results/ai-scanner-report.md
#
# Y también se publican en Vision One > AI Scanner.
# -------------------------------------------------------------------

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/security/ai-scanner/tmas-aiscan-llm-config.yaml"
RESULTS_DIR="$PROJECT_ROOT/.runtime/ai-scanner/results"
TMAS_BINARY="$PROJECT_ROOT/.runtime/ai-scanner/tmas"
REGION="eu-central-1"
mkdir -p "$(dirname "$TMAS_BINARY")"

echo ""
echo "========================================================"
echo "  TMAS AI Scanner — AI-untamiento de Trendo"
echo "  Objetivo: chatbot LLM (gpt-4o-mini / OpenAI)"
echo "========================================================"
echo ""

# -------------------------------------------------------------------
# Cargar .env.demo.local si existe y las variables no están ya exportadas
# -------------------------------------------------------------------
ENV_FILE="$PROJECT_ROOT/.env.demo.local"
if [ -f "$ENV_FILE" ]; then
  echo "[INFO] Cargando variables desde $ENV_FILE"
  set -a
  source "$ENV_FILE"
  set +a
fi

# -------------------------------------------------------------------
# Validar variables necesarias
# -------------------------------------------------------------------
if [ -z "$TMAS_API_KEY" ]; then
  echo "[ERROR] Falta TMAS_API_KEY. Exporta tu Vision One API key:"
  echo "        export TMAS_API_KEY=<tu_api_key>"
  exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
  echo "[ERROR] Falta OPENAI_API_KEY. Exporta tu API key de OpenAI:"
  echo "        export OPENAI_API_KEY=<tu_api_key>"
  exit 1
fi

# La config YAML referencia TARGET_API_KEY para el modelo objetivo
export TARGET_API_KEY="$OPENAI_API_KEY"

# -------------------------------------------------------------------
# Descargar el CLI de TMAS si no está presente
# -------------------------------------------------------------------
if [ ! -f "$TMAS_BINARY" ]; then
  echo "[INFO] CLI de TMAS no encontrado. Descargando..."

  OS=$(uname -s)
  ARCH=$(uname -m)

  if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    TMAS_URL="https://ast-cli.xdr.trendmicro.com/tmas-cli/latest/tmas-cli_Darwin_arm64.zip"
    EXT="zip"
  elif [ "$OS" = "Darwin" ]; then
    TMAS_URL="https://ast-cli.xdr.trendmicro.com/tmas-cli/latest/tmas-cli_Darwin_x86_64.zip"
    EXT="zip"
  elif [ "$OS" = "Linux" ] && [ "$ARCH" = "aarch64" ]; then
    TMAS_URL="https://ast-cli.xdr.trendmicro.com/tmas-cli/latest/tmas-cli_Linux_arm64.tar.gz"
    EXT="tar.gz"
  else
    TMAS_URL="https://ast-cli.xdr.trendmicro.com/tmas-cli/latest/tmas-cli_Linux_x86_64.tar.gz"
    EXT="tar.gz"
  fi

  TMP_FILE="/tmp/tmas-cli.$EXT"
  curl -sL "$TMAS_URL" -o "$TMP_FILE"

  if [ "$EXT" = "zip" ]; then
    unzip -q "$TMP_FILE" tmas -d "$(dirname "$TMAS_BINARY")"
  else
    tar -xzf "$TMP_FILE" -C "$(dirname "$TMAS_BINARY")" tmas
  fi

  chmod +x "$TMAS_BINARY"
  echo "[OK] TMAS CLI descargado en $TMAS_BINARY"
fi

# -------------------------------------------------------------------
# Preparar directorio de resultados
# -------------------------------------------------------------------
mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
JSON_OUTPUT="$RESULTS_DIR/ai-scanner-results_$TIMESTAMP.json"
MD_OUTPUT="$RESULTS_DIR/ai-scanner-report_$TIMESTAMP.md"

echo "[INFO] Configuración: $CONFIG_FILE"
echo "[INFO] Región: $REGION"
echo "[INFO] Resultados: $RESULTS_DIR/"
echo ""
echo "--------------------------------------------------------"
echo "  Iniciando escaneo de vulnerabilidades del modelo..."
echo "  (Esto puede tardar varios minutos)"
echo "--------------------------------------------------------"
echo ""

# -------------------------------------------------------------------
# Lanzar el escaneo
# -------------------------------------------------------------------
"$TMAS_BINARY" aiscan llm \
  -c "$CONFIG_FILE" \
  --region "$REGION" \
  --output "json=$JSON_OUTPUT,markdown=$MD_OUTPUT"

echo ""
echo "========================================================"
echo "  Escaneo completado"
echo "========================================================"
echo ""
echo "  Resultados JSON : $JSON_OUTPUT"
echo "  Informe Markdown: $MD_OUTPUT"
echo ""
echo "  Consulta el informe completo en:"
echo "  Vision One > Security for AI Stack > AI Scanner"
echo ""
