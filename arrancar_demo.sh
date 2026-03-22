#!/bin/zsh

BASE_DIR="/Users/alvaro_demiguel/Downloads/AI/atencion ciudadana"
BACKEND_DIR="$BASE_DIR/portal-backend"
FRONTEND_DIR="$BASE_DIR/portal-frontend"

echo "Cerrando procesos antiguos si existen..."
lsof -ti tcp:8007 | xargs kill -9 2>/dev/null || true
lsof -ti tcp:5173 | xargs kill -9 2>/dev/null || true

echo "Arrancando backend en nueva ventana..."
osascript -e "tell application \"Terminal\" to do script \"cd '$BACKEND_DIR' && ./arrancar_backend.sh\""

sleep 4

echo "Arrancando frontend en nueva ventana..."
osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_DIR' && ./arrancar_frontend.sh\""

echo ""
echo "Abre después:"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://127.0.0.1:8007"
echo "Swagger:  http://127.0.0.1:8007/docs"
