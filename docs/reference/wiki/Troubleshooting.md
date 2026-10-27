> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Troubleshooting

## Objetivo de esta página

Esta página recoge los problemas más frecuentes observados en la demo y cómo diagnosticarlos rápidamente.

Está organizada por síntomas, no por componentes, porque eso acelera mucho el troubleshooting en una demo real.

---

## Metodología recomendada

Cuando algo falla, la forma más eficiente de aislar el problema es separar estos planos:

1. frontend
2. proxy / conectividad
3. backend
4. AI Guard
5. OpenAI
6. File Security
7. Kubernetes

No conviene asumir que “si el frontal da error, el backend está caído”. En la práctica se vio que muchas veces el error visible en UI no coincide con la causa raíz.

---

## Síntoma: el frontend dice “No se ha podido conectar con el backend del chatbot”

### Diagnóstico rápido
Probar directamente el backend:

- `curl POST localhost:9000/api/chat`

Luego probar el frontend proxy:

- `curl POST localhost:8081/api/chat`

### Interpretación
- si falla 9000 y 8081 -> problema backend
- si funciona 9000 y falla 8081 -> problema de frontend/proxy
- si ambos devuelven 500 -> el backend está alcanzable pero falla internamente

### Caso real observado
El mensaje aparecía en el frontend, pero la causa real era una API key inválida de OpenAI.

---

## Síntoma: `/api/chat` devuelve 500

### Causa más frecuente observada
OpenAI API key inválida.

### Cómo detectarlo
Revisar logs del backend.

Indicador típico:
- `openai.AuthenticationError`
- `401 invalid_api_key`

### Explicación
AI Guard puede funcionar y bloquear prompts maliciosos, pero un prompt normal llega a OpenAI y falla allí. Eso genera un 500 interno en FastAPI.

### Solución
- recrear secret `trendo-secret`
- reiniciar backend

---

## Síntoma: AI Guard no bloquea lo que debería

### Comprobaciones
1. revisar logs del backend
2. confirmar que se llama a `call_trend_ai_guard()`
3. verificar:
   - TREND_API_KEY
   - TREND_AI_URL
   - TREND_AI_APP_NAME

### Interpretación
- si no aparece log de AI Guard -> problema de integración
- si AI Guard responde 400/401 -> problema de credencial o headers
- si responde Allow inesperado -> revisar caso de prueba o política

### Script útil
- `./scripts/troubleshooting_ai_guard.sh`

---

## Síntoma: backend en CreateContainerConfigError

### Causa típica
Falta un secret o una key dentro del secret.

### Comprobaciones
- `kubectl get secrets -n trendo-demo`
- `kubectl describe pod <backend-pod> -n trendo-demo`

### Secrets relevantes
- trendo-secret
- trendo-file-security
- trendo-ai

### Interpretación
Si falta cualquiera de ellos, el backend no podrá crear el contenedor correctamente.

---

## Síntoma: File Security devuelve `verdict=error`

### Causa frecuente
El backend alcanza la lógica de File Security, pero falla el scanner o la conectividad con él.

### Comprobaciones
- logs de backend
- existencia del service del scanner
- resolución DNS del scanner desde backend

### Errores típicos observados
- DNS resolution failed
- gRPC status code 14
- scanner host no encontrado

### Script útil
- `./scripts/troubleshooting_file_security.sh`

---

## Síntoma: DNS resolution failed para el scanner

### Causa típica
El namespace `visionone-filesecurity` no existe o el scanner no está desplegado.

### Comprobaciones
- `kubectl get ns`
- `kubectl get pods -n visionone-filesecurity`
- `kubectl get svc -n visionone-filesecurity`

### Interpretación
Si no existe el namespace o no existe el service:
- el backend no puede resolver el host interno

### Solución
Reinstalar o rebootstrapear File Security mediante el script completo.

---

## Síntoma: backend-communicator en CrashLoop o Init:CrashLoopBackOff

### Causa típica
Problema de onboarding de File Security.

### Comprobaciones
- logs del init container `init-token`
- secrets:
  - token-secret
  - device-token-secret

### Error real observado
- registration token inválido
- token-secret inexistente
- device-token-secret vacío

### Solución
- recrear los secrets correctos
- reinstalar Helm release

---

## Síntoma: scanner existe pero no está ready

### Explicación
Puede haber service y pod creado, pero el scanner no estar operativo todavía.

### Comprobaciones
- `kubectl get pods -n visionone-filesecurity`
- `kubectl describe pod ...`
- readiness

### Interpretación
No probar File Security hasta que:
- scanner esté ready
- backend-communicator no falle

---

## Síntoma: el script de despliegue falla al inicio

### Causas observadas
- `.env.demo.local` incompleto
- variables sin reemplazar
- puertos locales no definidos
- sintaxis de shell demasiado frágil

### Solución
Añadir validación temprana del fichero local y defaults razonables.

### Recomendación
El script debe fallar pronto y con mensaje claro, antes de tocar Kubernetes.

---

## Síntoma: el rollout se queda esperando a pods antiguos

### Causa típica
Pod viejo en terminating o nuevo pod que no llega a ready.

### Comprobaciones
- `kubectl get pods -n trendo-demo`
- `kubectl describe deployment backend -n trendo-demo`

### Interpretación
Normalmente no es problema de rollout en sí, sino de:
- secret mal cargado
- scanner no disponible
- backend roto

---

## Síntoma: port-forward no se puede abrir

### Causa típica
El puerto ya está en uso.

### Solución
Usar:
- `./scripts/parar_ports.sh`

O matar manualmente procesos de port-forward.

---

## Qué comprobar siempre, en este orden

Cuando algo no cuadre, la secuencia más útil es:

1. `kubectl get pods -n trendo-demo`
2. `kubectl get pods -n visionone-filesecurity`
3. `kubectl logs deployment/backend -n trendo-demo`
4. probar `curl` contra backend directo
5. probar `curl` vía frontend
6. revisar secrets
7. revisar scanner DNS

---

## Scripts de ayuda

- `scripts/troubleshooting_demo.sh`
- `scripts/troubleshooting_ai_guard.sh`
- `scripts/troubleshooting_file_security.sh`
- `scripts/apagar_demo_full.sh`
- `scripts/parar_ports.sh`

---

## Idea clave

El troubleshooting rápido de esta demo consiste en no adivinar.

Siempre conviene comprobar por separado:

- conectividad
- autenticación
- Kubernetes
- scanner
- modelo LLM

Eso evita perder tiempo persiguiendo síntomas equivocados.