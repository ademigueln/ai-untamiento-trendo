#!/bin/bash

set -euo pipefail
umask 077
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/.local/px.env"
: "${GROQ_API_KEY:?Configura .local/px.env}"
: "${TREND_API_KEY:?Configura .local/px.env}"
: "${FILE_SECURITY_API_KEY:?Configura .local/px.env}"

LOG="/var/log/ai-untamiento-deploy.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date)] Iniciando despliegue..."

# =============================================================================
# Credenciales — rellena estos valores antes de usar el script
# =============================================================================
# =============================================================================

REPO_URL="https://github.com/t741712-afk/ai-untamiento-trendo.git"
DEST_DIR="/opt/ai-untamiento"

# --- Docker -------------------------------------------------------------------
echo "[$(date)] Instalando Docker..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -qq
apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
echo "[$(date)] Docker instalado: $(docker --version)"

# --- Repo ---------------------------------------------------------------------
echo "[$(date)] Clonando repo..."
git clone "$REPO_URL" "$DEST_DIR"

# --- .env ---------------------------------------------------------------------
echo "[$(date)] Generando .env..."
cat > "$DEST_DIR/.env" <<EOF
BACKEND_PORT=9000
FRONTEND_PORT=80
UPLOAD_DIR=/data/uploads
EOF

# --- Arrancar -----------------------------------------------------------------
echo "[$(date)] Lanzando contenedores..."
cd "$DEST_DIR"
docker compose up -d --build

echo "[$(date)] Despliegue completado. Frontend en http://$(hostname -I | awk '{print $1}')"
