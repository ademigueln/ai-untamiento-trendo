# TREND_TMAS_CICD.md

# Trend Micro Artifact Scanner (TMAS) – Integración en CI/CD

## Descripción

TMAS se ha integrado en GitHub Actions para añadir una capa de seguridad de pipeline.

Se han definido dos workflows:

1. Escaneo del repositorio
2. Escaneo de imágenes Docker

---

## Requisitos

En GitHub se creó el secret:

TMAS_API_KEY

Ruta en GitHub:

Settings -> Secrets and variables -> Actions

---

## Región utilizada

Para esta demo se utiliza:

eu-central-1

Se pasa a TMAS mediante:

additionalArgs: --region=eu-central-1

---

## Workflow 1 – Repo Scan

Fichero:

.github/workflows/tmas-repo-scan.yml

Objetivo:

Escanear el contenido del repositorio en cada push a main, pull request y ejecución manual.

Conceptos clave usados:

- actions/checkout@v4
- trendmicro/tmas-scan-action@v3.1.3
- artifact: dir:./repo

Capacidades activadas:

- vulnerabilitiesScan: true
- secretsScan: true
- malwareScan: false

Resumen funcional:

1. Se hace checkout del repo
2. TMAS analiza el directorio
3. Se buscan:
   - vulnerabilidades OSS
   - secretos en código

---

## Workflow 2 – Image Scan

Fichero:

.github/workflows/tmas-image-scan.yml

Objetivo:

Escanear imágenes Docker publicadas en registry.

Artefactos utilizados:

- registry:drdro28/trendo-backend:0.3.3
- registry:drdro28/trendo-frontend:0.1.3

Capacidades activadas:

- vulnerabilitiesScan: true
- malwareScan: true
- secretsScan: true

Resumen funcional:

1. TMAS descarga la imagen desde el registry
2. Analiza:
   - CVEs
   - malware
   - secretos
3. Devuelve findings en GitHub Actions

---

## Problemas resueltos durante la integración

### Versión de la action

Inicialmente se intentó usar:

trendmicro/tmas-scan-action@v2

Esto falló porque ese tag no existía.

Se corrigió a:

trendmicro/tmas-scan-action@v3.1.3

### Trigger manual

Para poder lanzar workflows manualmente desde la UI de GitHub se añadió:

workflow_dispatch:

Sin ese bloque no aparece el botón "Run workflow".

### Push de workflows

GitHub rechazó inicialmente el push porque el PAT no tenía permiso para modificar workflows.

Se solucionó usando un token con scope:

- repo
- workflow

---

## Valor de la integración

TMAS cubre la capa de seguridad previa al despliegue:

- código fuente
- imágenes Docker
- artefactos

De esta forma la demo cubre:

- runtime documental
- runtime IA
- pipeline / CI-CD

====================================================================