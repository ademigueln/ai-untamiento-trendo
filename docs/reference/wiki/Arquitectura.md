> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Arquitectura

## Objetivo de esta página

Esta página describe la arquitectura técnica de la demo AI-untamiento de Trendo y cómo se relacionan entre sí los distintos componentes funcionales y de seguridad.

La intención no es documentar cada fichero al detalle, sino explicar:

- qué piezas existen
- cómo se comunican
- qué dependencias son críticas
- qué partes son reutilizables en cliente

---

## Visión general

La demo está construida sobre tres planos principales:

1. Plano de experiencia de usuario
2. Plano de lógica de negocio
3. Plano de seguridad

### 1. Plano de experiencia de usuario
Incluye el frontend React que presenta:

- chatbot
- subida de archivos
- dashboard de estado
- indicadores de seguridad

### 2. Plano de lógica de negocio
Incluye el backend FastAPI que:

- recibe peticiones del frontend
- llama a AI Guard
- llama al modelo LLM
- llama al scanner de File Security
- devuelve respuestas al frontend

### 3. Plano de seguridad
Incluye tres mecanismos:

- AI Guard para protección del flujo conversacional
- File Security para protección de archivos
- TMAS para protección del pipeline

---

## Componentes de la solución

## Frontend

Tecnología:
- React

Ubicación:
- portal-frontend/

Responsabilidades:
- mostrar la interfaz de la sede electrónica
- enviar prompts al backend
- subir archivos al backend
- mostrar métricas
- mostrar veredictos de seguridad

Puntos clave:
- el frontend no habla directamente con Trend
- el frontend habla solo con el backend mediante `/api/...`
- el proxy Nginx reenvía `/api/` al backend

---

## Backend

Tecnología:
- FastAPI

Ubicación:
- portal-backend/

Responsabilidades:
- exponer endpoints REST
- aplicar lógica de negocio
- integrar AI Guard
- integrar File Security
- integrar el modelo LLM
- consolidar resultados para la UI

Endpoints principales:
- `/api/chat`
- `/api/files/upload`
- `/api/stats`

Puntos clave:
- el backend es el punto central de orquestación
- la seguridad no está implementada en frontend
- toda la lógica sensible está en backend

---

## AI Guard

Tipo:
- servicio cloud

Función:
- analizar prompts de entrada
- analizar respuestas del modelo
- devolver acción Allow o Block

Dependencia:
- API key de Trend Vision One
- endpoint regional EU
- nombre de aplicación

---

## File Security

Tipo:
- scanner contenerizado desplegado en Kubernetes

Función:
- analizar los archivos que sube el usuario
- devolver veredicto técnico
- exponer un endpoint gRPC accesible desde el backend

Dependencia:
- namespace de Kubernetes
- release Helm
- registration token
- DNS interno del servicio scanner

---

## TMAS

Tipo:
- GitHub Action / CI-CD scanner

Función:
- escanear repositorio
- escanear imágenes Docker
- detectar vulnerabilidades, malware y secretos

Dependencia:
- TMAS_API_KEY
- workflows de GitHub Actions

---

## Flujos principales

## Flujo de chat

Secuencia lógica:

1. El usuario escribe un mensaje en el frontend
2. El frontend llama a `/api/chat`
3. El backend ejecuta AI Guard sobre el input
4. Si el input está permitido, el backend llama al modelo
5. La respuesta del modelo pasa por AI Guard
6. El backend devuelve la respuesta final al frontend

Representación simplificada:

Usuario -> Frontend -> Backend -> AI Guard input -> LLM -> AI Guard output -> Frontend

---

## Flujo de subida de archivos

Secuencia lógica:

1. El usuario selecciona un archivo
2. El frontend llama a `/api/files/upload`
3. El backend guarda temporalmente el archivo en `/incoming`
4. El backend llama al scanner de File Security
5. El scanner devuelve el resultado
6. El backend mueve el archivo según el veredicto
7. El frontend muestra el resultado y actualiza métricas

Representación simplificada:

Usuario -> Frontend -> Backend -> incoming -> File Security -> clean/quarantine -> Frontend

---

## Flujo de CI/CD

Secuencia lógica:

1. Se hace push al repositorio
2. GitHub Actions ejecuta workflows TMAS
3. TMAS analiza repo o imágenes
4. Se generan findings

Representación simplificada:

GitHub -> TMAS -> findings

---

## Kubernetes

La demo usa dos namespaces diferenciados.

## Namespace `trendo-demo`

Contiene:
- backend
- frontend
- services de backend y frontend
- PVC de uploads
- secrets de la aplicación

Este namespace representa la propia aplicación.

## Namespace `visionone-filesecurity`

Contiene:
- scanner
- management-service
- backend-communicator
- scan-cache
- secrets propios del scanner

Este namespace representa la infraestructura de File Security.

---

## Dependencias críticas

Estas son las dependencias que más suelen romper la demo.

### 1. Secrets correctos
Si faltan o son inválidos:
- backend no arranca
- AI Guard falla
- OpenAI falla
- File Security no termina onboarding

### 2. Scanner disponible
El backend depende de que exista el servicio:

my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

### 3. OpenAI API key válida
Si la key es inválida:
- AI Guard puede seguir funcionando
- pero el chat normal devuelve 500

### 4. Orden de despliegue
El orden correcto es:
1. namespaces
2. secrets
3. File Security
4. backend/frontend
5. port-forward

---

## Ficheros importantes del proyecto

Frontend:
- portal-frontend/src/App.jsx
- portal-frontend/src/index.css
- portal-frontend/nginx.conf

Backend:
- portal-backend/app/routes/chat.py
- portal-backend/app/routes/files.py
- portal-backend/app/services/chatbot.py
- portal-backend/app/services/ai_guard.py
- portal-backend/app/services/file_security.py
- portal-backend/app/services/storage.py
- portal-backend/app/services/stats.py

Kubernetes:
- k8s/backend.yaml
- k8s/frontend.yaml
- k8s/namespace.yaml
- k8s/pvc.yaml
- k8s/secret.yaml.template

Scripts:
- scripts/desplegar_demo_full.sh
- scripts/apagar_demo_full.sh
- scripts/troubleshooting_demo.sh
- scripts/troubleshooting_ai_guard.sh
- scripts/troubleshooting_file_security.sh

---

## Qué partes son genéricas y reutilizables

Se pueden reutilizar casi directamente:

- patrón de AI Guard input/output
- patrón de File Security con staging incoming/clean/quarantine
- patrón de despliegue con secrets + Helm + app
- patrón de troubleshooting por síntomas

Lo que normalmente cambiaría en cliente:

- branding y frontend
- prompts del chatbot
- proveedor de modelo LLM
- naming de namespaces
- almacenamiento persistente
- auditoría y logging corporativo

---

## Idea clave

La arquitectura no protege solo el modelo ni solo los archivos. Protege el ciclo completo:

- entrada conversacional
- salida conversacional
- entrada documental
- build pipeline

Ese es el valor principal de la demo y también la razón por la que sirve como base reutilizable para cliente.