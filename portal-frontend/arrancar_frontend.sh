#!/bin/zsh

cd "/Users/alvaro_demiguel/Downloads/AI/atencion ciudadana/portal-frontend" || exit 1

FRONTEND_PORT="5173"

echo "Parando frontend anterior si existe..."
lsof -ti tcp:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

if [ ! -d "node_modules" ]; then
  echo "No existe node_modules. Instalo dependencias..."
  npm install
fi

echo "Arrancando frontend en puerto $FRONTEND_PORT..."
npm run dev -- --host 0.0.0.0
