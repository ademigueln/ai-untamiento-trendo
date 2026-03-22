# 🏛️ AI-untamiento de Trendo

Portal demo de administración pública con capacidades de IA, diseñado para demostrar casos de uso reales de seguridad en aplicaciones modernas (chatbot LLM + gestión documental).

---

## 🎯 Objetivo

Simular un portal de atención al ciudadano donde:

- los usuarios pueden subir documentos
- interactúan con un chatbot basado en IA
- existe un flujo de procesamiento de archivos
- se puede integrar seguridad (TrendAI / File Security / AI Guardrails)

---

## 🧱 Arquitectura
Frontend (React + Nginx)
↓
Ingress / Service
↓
Backend (FastAPI)
↓
Storage (PVC)

### Componentes

- **Frontend**: React + Vite → servido con Nginx
- **Backend**: FastAPI (Python)
- **IA**: OpenAI API
- **Storage**:
  - incoming/
  - clean/
  - quarantine/
- **Infra**:
  - Docker
  - Kubernetes
  - Ingress

---

## 📁 Estructura del proyecto
ai-untamiento-trendo/
├── portal-backend/
├── portal-frontend/
├── k8s/
├── docker-compose.yml
├── README.md
├── .env.example
├── .env.docker.example
---

## ⚙️ Requisitos

- Docker
- Kubernetes (Docker Desktop o cluster)
- kubectl
- cuenta OpenAI (API Key)

---

## 🚀 Ejecución local (sin Docker)

### Backend

```bash
cd portal-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8007

### Frontend

cd portal-frontend
npm install
npm run dev

🐳 Ejecución con Docker
docker compose up --build

### ACCESO
http://localhost:5173


☸️ Despliegue en Kubernetes

1. Clonar repositorio
git clone https://github.com/ademigueln/ai-untamiento-trendo.git
cd ai-untamiento-trendo

2. Crear secret (RECOMENDADO)
kubectl create secret generic trendo-secret \
  -n trendo-demo \
  --from-literal=OPENAI_API_KEY="TU_API_KEY"

  3. Desplegar recursos
  kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml

4. Acceso

Opción A — port-forward
kubectl port-forward -n trendo-demo service/frontend-service 8081:80

Opción B — Ingress
http://ai-untamiento.trendo.local
(Configurando /etc/hosts)

📦 Publicación de imágenes
### Backend
docker build -t trendo-backend .
docker tag trendo-backend drdro28/trendo-backend:0.1.0
docker push drdro28/trendo-backend:0.1.0

### Frontend
docker build -t trendo-frontend .
docker tag trendo-frontend drdro28/trendo-frontend:0.1.0
docker push drdro28/trendo-frontend:0.1.0

🔐 Seguridad (roadmap)

Este portal está diseñado para integrar:
	•	AI Application Security (OWASP Top 10 LLM)
	•	Guardrails para IA
	•	File Security (análisis de ficheros)
	•	detección de contenido malicioso
	•	auditoría de uso de IA

⸻

📊 Funcionalidades actuales
	•	subida de documentos
	•	clasificación (clean / quarantine)
	•	chatbot IA
	•	dashboard de estadísticas
	•	persistencia en almacenamiento

⸻

⚠️ Notas importantes
	•	NO subir API keys al repositorio
	•	usar .env o Kubernetes Secrets
	•	rotar claves si se exponen

⸻

🚀 Próximos pasos
	•	integración con TrendAI
	•	guardrails en chatbot
	•	escaneo de ficheros
	•	observabilidad
	•	autenticación de usuarios

⸻

👨‍💻 Autor

Álvaro de Miguel

---

# PASO 3 — guardar

Pulsa:

- `CTRL + X`
- `Y`
- `ENTER`

---

# PASO 4 — subir README a GitHub

Ahora copia y pega esto:

```bash
git add README.md
git commit -m "Add professional README"
git push


