> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# AI Scanner — Escaneo de vulnerabilidades del modelo LLM

## Qué es el AI Scanner

El AI Scanner de TMAS (Trend Micro Artifact Scanner) es una herramienta que lanza ataques controlados contra el modelo LLM del chatbot para detectar vulnerabilidades **antes de que lleguen a producción**.

Complementa a AI Guard, que protege el sistema en tiempo de ejecución (runtime). El AI Scanner opera en tiempo de build o pre-despliegue.

La diferencia clave entre ambos:

| | AI Guard | AI Scanner |
|---|---|---|
| Cuándo actúa | Runtime (cada petición) | Pre-deploy (CI/CD o manual) |
| Qué protege | Conversaciones del usuario | El propio modelo LLM |
| Tipo de protección | Guardarrailes en tiempo real | Test de vulnerabilidades |
| Resultado | Allow / Block por petición | Informe de hallazgos del modelo |

---

## Qué escanea en esta demo

El escáner ataca el endpoint OpenAI (gpt-4o-mini) con los siguientes objetivos:

- **Prompt Injection** — ¿puede un atacante inyectar instrucciones que anulen el system prompt del chatbot?
- **Sensitive Data Leak** — ¿el modelo filtra información confidencial o de expedientes que no debería revelar?
- **Harmful Content** — ¿el modelo genera contenido dañino, ofensivo o inapropiado?
- **Jailbreak** — ¿técnicas de evasión consiguen saltarse las restricciones del modelo?
- **Social Engineering** — ¿el modelo puede ser manipulado para dar información a quien no le corresponde?
- **Hallucination** — ¿el modelo inventa normativas, plazos o procedimientos municipales con apariencia oficial?

---

## Cómo está integrado en el proyecto

### Ficheros añadidos

```
ai-scanner/
  tmas-aiscan-llm-config.yaml   ← configuración del escáner
  results/                      ← resultados locales (gitignored)

.github/workflows/
  tmas-ai-scanner.yml           ← workflow de CI/CD

scripts/
  run_ai_scanner.sh             ← lanzamiento local
```

### Cuándo se lanza automáticamente (CI/CD)

El workflow `tmas-ai-scanner.yml` se ejecuta en GitHub Actions cuando hay un push a `main` o un Pull Request que afecta a:

- `portal-backend/app/services/chatbot.py`
- `portal-backend/app/services/ai_guard.py`
- `portal-backend/app/routes/chat.py`
- `ai-scanner/**`

También puede lanzarse manualmente desde **Actions > TMAS AI Scanner**.

Los resultados se publican automáticamente como comentario en el Pull Request y se guardan como artefactos descargables (JSON + Markdown) durante 30 días.

---

## Lanzamiento local (modo demo)

### Requisitos previos

1. Tener `TMAS_API_KEY` y `OPENAI_API_KEY` en `.env.demo.local`
2. La API key de Vision One debe tener un rol con permisos de AI Scanner

### Ejecución

```bash
./scripts/run_ai_scanner.sh
```

El script:
1. Carga las variables desde `.env.demo.local`
2. Descarga el CLI de TMAS si no está presente en `ai-scanner/tmas`
3. Lanza el escaneo contra gpt-4o-mini
4. Guarda los resultados en `ai-scanner/results/`
5. Publica los hallazgos en Vision One

### Ver resultados

- **Local:** `ai-scanner/results/ai-scanner-report_*.md`
- **Vision One:** Security for AI Stack → AI Scanner → grupo `ai-untamiento-trendo-chatbot`

---

## Modo interactivo (exploración)

Para explorar manualmente las opciones del escáner y generar una configuración base:

```bash
export TMAS_API_KEY=<tu_key>
./ai-scanner/tmas aiscan llm -i --region eu-central-1
```

El wizard interactivo permite seleccionar el tipo de target, introducir el endpoint y la API key del modelo, y elegir los objetivos de ataque. Al final ofrece guardar la configuración como YAML.

---

## Dependencias y secrets necesarios

| Variable | Descripción | Dónde configurar |
|---|---|---|
| `TMAS_API_KEY` | Vision One API key con permisos AI Scanner | `.env.demo.local` y GitHub Secret |
| `OPENAI_API_KEY` | API key de OpenAI (modelo objetivo del escaneo) | `.env.demo.local` y GitHub Secret |

El Secret `OPENAI_API_KEY` ya está en uso para el backend. Solo necesitas añadir `TMAS_API_KEY` como nuevo Secret en GitHub si no lo tenías.

---

## Relación con el resto de la arquitectura de seguridad

```
Pre-deploy                      Runtime
─────────────────               ──────────────────────────────────
TMAS AI Scanner   ──────────►  AI Guard (input + output)
  Escanea el                     Protege cada conversación
  modelo LLM                     en tiempo real

TMAS Repo Scan    ──────────►  File Security (gRPC)
  Escanea el                     Escanea cada archivo
  código fuente                  subido por el ciudadano

TMAS Image Scan   ──────────►  (Kubernetes hardening)
  Escanea las
  imágenes Docker
```

Los tres niveles de TMAS cubren el pipeline antes de llegar a producción. AI Guard y File Security cubren el sistema una vez desplegado.
