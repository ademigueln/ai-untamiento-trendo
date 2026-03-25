# AI-untamiento de Trendo

Demo end-to-end de protección de aplicaciones con IA y canal documental seguro utilizando capacidades de Trend Micro (Trend Vision One / TrendAI).

El proyecto simula una sede electrónica municipal con:

- Chatbot basado en LLM
- Subida de documentación por parte de la ciudadanía
- Dashboard de actividad
- Integración de seguridad en tiempo real
- Despliegue reproducible mediante un único script

---

# Arquitectura

## Frontend
- React SPA
- Chat IA
- Subida de archivos
- Dashboard

## Backend (FastAPI)
- /api/chat
- /api/files/upload
- /api/stats

## Seguridad

### AI Guard
- Protección frente a prompt injection
- Control de contenido
- Protección de salida del modelo

### File Security (contenarizado)
- Scanner desplegado en Kubernetes
- Comunicación gRPC interna

### TMAS
- Escaneo de repo
- Escaneo de imágenes Docker

---

# Flujo

## Chat
1. Usuario → backend
2. Backend → AI Guard (input)
3. Si OK → LLM
4. LLM → AI Guard (output)
5. Respuesta al usuario

## Archivos
1. Upload → incoming
2. Scan File Security
3. Resultado:
   - clean → clean/
   - malicious → quarantine/
   - error → incoming/

---

# Arranque de la demo

## Script principal
./scripts/desplegar_demo_full.sh

## Qué hace

- Valida Docker y Kubernetes
- Genera secrets desde plantilla
- Despliega File Security
- Despliega backend/frontend
- Abre port-forwards

---

# Configuración

NO se suben secrets a Git.

Se usa:
.env.demo.local

## Uso
cp .env.demo.local.example .env.demo.local
nano .env.demo.local
./scripts/desplegar_demo_full.sh

---

# Secrets (modo seguro)

NO se suben:

- .env.demo.local
- k8s/secret.yaml
- k8s/file-security-secrets.yaml

SÍ se suben:

- k8s/secret.yaml.template
- .env.demo.local.example

El script genera automáticamente:

- k8s/secret.yaml
- k8s/file-security-secrets.yaml

---

# File Security

Namespace: visionone-filesecurity
Scanner: my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

---

# Troubleshooting
./scripts/troubleshooting_demo.sh
./scripts/troubleshooting_ai_guard.sh
./scripts/troubleshooting_file_security.sh

---

# Apagado completo
./scripts/apagar_demo_full.sh

---

# Acceso

Frontend: http://localhost:8081
Backend: http://localhost:9000/api/stats

---

# TL;DR
git clone https://github.com/ademigueln/ai-untamiento-trendo.git
cd ai-untamiento-trendo
cp .env.demo.local.example .env.demo.local
nano .env.demo.local
./scripts/desplegar_demo_full.sh

---

# Autor

Álvaro de Miguel

