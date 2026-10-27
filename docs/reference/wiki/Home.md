> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# AI-untamiento de Trendo

## Qué es esta demo

AI-untamiento de Trendo es una demo de sede electrónica protegida con capacidades de seguridad de Trend Micro para dos planos distintos:

- plano conversacional: protección del chatbot con AI Guard
- plano documental: protección de los ficheros subidos con File Security

Además, el proyecto incorpora protección de pipeline con TMAS en GitHub Actions.

## Qué demuestra

La demo enseña un patrón completo de protección en aplicaciones modernas con IA:

- inspección de prompts y respuestas del modelo
- inspección de archivos subidos por el usuario
- validación de artefactos en CI/CD

## Componentes principales

- Frontend React
- Backend FastAPI
- Trend AI Guard
- Trend Vision One File Security en modo contenerizado
- TMAS en GitHub Actions
- Kubernetes local para ejecución de la demo

## Flujo funcional

### Chat
Usuario -> Backend -> AI Guard input -> LLM -> AI Guard output -> Usuario

### Ficheros
Usuario -> Backend -> incoming -> File Security scanner -> clean/quarantine

### Pipeline
GitHub -> TMAS -> findings sobre repo e imágenes

## Páginas de esta wiki

- Arquitectura
- AI Guard
- File Security
- Despliegue end-to-end
- Troubleshooting
- Reutilización en cliente

## Ruta del código

- backend: portal-backend/
- frontend: portal-frontend/
- manifests k8s: k8s/
- scripts: scripts/
- documentación complementaria: docs/

## Objetivo de esta wiki

Esta wiki no pretende documentar la demo de forma estática, sino servir como referencia práctica para:

- entender cómo está implementada
- desplegarla desde cero
- depurar fallos
- reutilizar el patrón en cliente