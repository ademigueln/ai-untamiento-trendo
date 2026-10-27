# AI Guard

La integración vive en `portal-backend/app/services/ai_guard.py`; la ruta de chat coordina la inspección de entrada, el proveedor LLM y la inspección de salida.

## Configuración

`.env.demo.local` aporta `TREND_API_KEY`, `TREND_AI_URL` y `TREND_AI_APP_NAME`. El arranque genera el secreto `trendo-ai` y el manifiesto del backend referencia esas claves. `GUARD_FAIL_OPEN` se configura en `k8s/config.yaml`; su valor predeterminado es `false`.

El endpoint EU configurado en el ejemplo es `https://api.eu.xdr.trendmicro.com/v3.0/aiSecurity/applyGuardrails`. La petición usa autorización Bearer, `TMV1-Application-Name`, `Prefer: return=representation` y JSON con el campo `prompt`.

La fase de entrada o salida se distingue dentro de la aplicación. El payload actual envía únicamente el texto que se inspecciona; no declara un campo de dirección a la API externa.

## Decisiones

- `Allow`: permite continuar esa fase.
- `Block`: interrumpe el flujo con una respuesta de política.
- Error, acción desconocida o estructura inválida: servicio no verificable; en modo estricto el portal devuelve indisponibilidad.

Una entrada bloqueada no llama al modelo. Una salida bloqueada no se devuelve ni se incorpora al historial. En modo permisivo se puede mostrar una respuesta degradada, sin conservarla como contexto aprobado.

## Eventos y diagnóstico

SQLite registra metadatos de la consulta y su resultado, con retención y capacidad limitadas. No se conservan prompts ni respuestas. Las categorías de bloqueo se derivan de los motivos de AI Guard para mostrar los contadores de la demo.

```sh
./scripts/troubleshooting_ai_guard.sh
```

El diagnóstico envía una petición real. El resultado depende de la política configurada y del estado del servicio. Las pruebas automatizadas sustituyen las dependencias externas y comprueban las decisiones locales; no certifican la eficacia de una política remota.
