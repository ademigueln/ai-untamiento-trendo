# TREND_SECURITY_ARCHITECTURE.md

# Arquitectura de Seguridad – AI-untamiento de Trendo

## Visión general

La demo se ha diseñado para demostrar protección en varias capas de una aplicación moderna con IA.

Se cubren tres planos:

1. Documentos
2. Chatbot IA
3. Pipeline de desarrollo

---

## Capa 1 – File Security

Protege la subida de archivos de la ciudadanía.

Función:

- Analizar archivos en tiempo real
- Detectar malware
- Clasificar el contenido

Tecnología usada:

Trend Vision One File Security – Containerized Scanner

Ubicación:

Dentro de Kubernetes

---

## Capa 2 – AI Guard

Protege el uso del LLM.

Función:

- Inspección de prompts
- Detección de prompt injection
- Revisión de salidas del modelo
- Aplicación de guardrails gestionados por Trend

Tecnología usada:

Trend Vision One AI Guard

Ubicación:

API cloud EU

---

## Capa 3 – TMAS

Protege el pipeline de desarrollo.

Función:

- Escanear el código
- Escanear imágenes Docker
- Detectar vulnerabilidades, malware y secretos

Tecnología usada:

Trend Micro Artifact Scanner (TMAS)

Ubicación:

GitHub Actions

---

## Flujo completo de seguridad

### Flujo documental

Usuario -> Frontend -> Backend -> File Security Scanner -> clean/quarantine

### Flujo IA

Usuario -> Frontend -> Backend -> AI Guard -> LLM -> AI Guard -> Usuario

### Flujo CI/CD

Git push -> GitHub Actions -> TMAS -> Findings

---

## Objetivo de la demo

Mostrar seguridad integrada en todo el ciclo de una aplicación:

- Build time
- Run time documental
- Run time IA

---

## Mensaje clave

La seguridad en aplicaciones con IA no debe limitarse a proteger el modelo.

Debe cubrir:

- archivos de entrada
- prompts
- respuestas
- artefactos de despliegue
- pipeline de desarrollo

====================================================================

# Cómo crear estos ficheros en tu repo

Crea cada documento así:

nano TREND_FILE_SECURITY_DEPLOYMENT.md
nano TREND_AI_GUARD_DEPLOYMENT.md
nano TREND_TMAS_CICD.md
nano TREND_SECURITY_ARCHITECTURE.md

Pega el contenido correspondiente en cada fichero y guarda.

====================================================================

# Cómo subirlos a Git

git add TREND_FILE_SECURITY_DEPLOYMENT.md TREND_AI_GUARD_DEPLOYMENT.md TREND_TMAS_CICD.md TREND_SECURITY_ARCHITECTURE.md
git commit -m "Add Trend deployment documentation"
git push