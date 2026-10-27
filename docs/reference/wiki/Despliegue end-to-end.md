> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Despliegue end-to-end

## Objetivo de esta página

Esta página explica cómo se levanta la demo completa desde cero y qué hace exactamente el script de despliegue.

La idea es que esta página sirva como referencia operativa para:

- compañeros que necesiten arrancar la demo
- troubleshooting
- reutilización del proceso en entornos de cliente o laboratorio

---

## Filosofía del despliegue

La demo debe poder levantarse desde cero sin depender de acciones manuales dispersas.

Por eso se ha trabajado para concentrar el bootstrap en un único script principal:

- scripts/desplegar_demo_full.sh

Ese script no compila la aplicación desde cero ni reconstruye imágenes. Su objetivo es preparar el entorno, generar secretos locales y desplegar los componentes en el orden correcto.

---

## Qué necesita el operador antes de lanzar el script

Necesitas:

1. repositorio clonado
2. Docker Desktop operativo
3. Kubernetes operativo
4. kubectl operativo
5. Helm operativo
6. fichero local `.env.demo.local` con credenciales
7. Las secrets/ApiKeys que vinculan el entorno demo con las soluciones de TrendAI, debes copiar el fichero de texto en el path

---

## Ficheros de configuración usados

## `.env.demo.local`
Es el fichero local con las variables sensibles necesarias para la demo.

No se sube al repositorio.

Se crea a partir de:

- `.env.demo.local.example`

Variables principales:

- OPENAI_API_KEY
- TREND_API_KEY
- FILE_SECURITY_API_KEY
- FILE_SECURITY_REGISTRATION_TOKEN
- TREND_AI_URL
- TREND_AI_APP_NAME
- FILE_SECURITY_HOST

## `k8s/secret.yaml.template`
Plantilla de secrets del namespace de la aplicación.

No contiene secretos reales, solo placeholders.

## `k8s/secret.yaml`
Lo genera el script localmente a partir de la plantilla y del `.env.demo.local`.

## `k8s/file-security-secrets.yaml`
Lo genera el script localmente para el namespace de File Security.

---

## Qué hace el script de despliegue

## Paso 1. Validar configuración local
Comprueba que existe `.env.demo.local`.

Después valida que variables críticas no estén vacías.
Esto evita desplegar una demo rota por falta de claves.

## Paso 2. Validar Docker
Comprueba que Docker Desktop responde.

Si no responde, intenta abrirlo y espera hasta que esté operativo.

## Paso 3. Validar Kubernetes
Comprueba que `kubectl cluster-info` responde.

Si Kubernetes no está listo, espera un tiempo razonable antes de abortar.

## Paso 4. Crear namespaces
Asegura la existencia de:

- trendo-demo
- visionone-filesecurity

## Paso 5. Generar `k8s/secret.yaml`
Renderiza la plantilla de secrets de la aplicación usando variables reales del fichero local.

## Paso 6. Generar `k8s/file-security-secrets.yaml`
Construye el secret con:

- registration token para File Security
- device-token-secret inicial

## Paso 7. Aplicar secrets
Aplica:

- secret de app
- secret de AI Guard
- secret de File Security

## Paso 8. Instalar o actualizar File Security
Ejecuta Helm para desplegar o actualizar el chart de Trend Vision One File Security.

## Paso 9. Esperar readiness de File Security
No basta con instalar el chart. El script espera explícitamente a que los deployments críticos estén listos.

## Paso 10. Aplicar backend y frontend
Aplica los manifests de la aplicación.

## Paso 11. Reiniciar despliegues
Reinicia backend y frontend para que cojan los secrets nuevos.

## Paso 12. Verificar DNS interno del scanner
Hace una comprobación práctica desde el backend para confirmar que resuelve el host del scanner.

## Paso 13. Abrir port-forward
Levanta:

- backend en localhost:9000
- frontend en localhost:8081

---

## Orden correcto de despliegue

El orden importa mucho.

Orden real que debe respetarse:

1. Docker
2. Kubernetes
3. namespaces
4. secrets
5. File Security
6. backend/frontend
7. port-forward
8. validación funcional

Si se altera este orden, son frecuentes estos fallos:

- backend arrancando sin scanner disponible
- File Security sin onboarding correcto
- API keys no refrescadas en backend
- frontend operativo pero backend roto

---

## Validaciones mínimas post-despliegue

Una vez terminado el script, deberían validarse tres cosas.

## 1. Backend responde
Ejemplo:
- `/api/stats`

## 2. AI Guard protege prompts maliciosos
Ejemplo:
- prompt injection bloqueado

## 3. File Security analiza archivos
Ejemplo:
- subida de fichero con resultado válido

---

## Qué scripts complementarios existen

## `scripts/apagar_demo_full.sh`
Simula apagado completo de la demo:

- borra namespaces relevantes
- elimina despliegues
- elimina release Helm
- mata port-forwards

Sirve para probar el bootstrap desde cero.

## `scripts/troubleshooting_demo.sh`
Comprueba estado global de la demo.

## `scripts/troubleshooting_ai_guard.sh`
Aísla la validación de AI Guard.

## `scripts/troubleshooting_file_security.sh`
Aísla la validación de File Security.

## `scripts/parar_ports.sh`
Mata port-forwards sin tocar el resto del entorno.

---

## Errores más comunes en despliegue

## 1. Falta de secrets
Síntoma:
- backend en CreateContainerConfigError

## 2. File Security no termina onboarding
Síntoma:
- backend-communicator en CrashLoop
- scanner no ready

## 3. OpenAI API key inválida
Síntoma:
- `/api/chat` devuelve 500 para prompts normales
- prompts bloqueados por AI Guard siguen pareciendo “correctos”

## 4. Port-forward ya ocupado
Síntoma:
- no se puede abrir 9000 o 8081

---

## Recomendaciones operativas

- validar siempre con `apagar_demo_full.sh` seguido de `desplegar_demo_full.sh`
- no asumir que Kubernetes mantiene el estado tras reinicios
- no asumir que un pod `Running` implica servicio usable
- validar siempre AI Guard, File Security y OpenAI por separado

---

## Idea clave

El valor del despliegue no está solo en “levantar pods”, sino en comprobar que la cadena entera queda funcional:

- scanner listo
- backend autenticado
- LLM operativo
- frontend conectado

Ese enfoque es el que hace que la demo sea realmente reproducible.
