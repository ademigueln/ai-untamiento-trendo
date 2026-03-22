#!/bin/zsh

cd "/Users/alvaro_demiguel/Downloads/AI/atencion ciudadana/portal-backend" || exit 1

BACKEND_PORT="8007"

echo "Parando backend anterior si existe..."
lsof -ti tcp:$BACKEND_PORT | xargs kill -9 2>/dev/null || true

if [ ! -d ".venv" ]; then
  echo "No existe .venv. Lo creo ahora..."
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Arrancando backend en puerto $BACKEND_PORT..."
uvicorn main:app --reload --port $BACKEND_PORT
