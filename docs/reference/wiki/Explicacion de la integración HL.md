> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Explicacion de la integración HL

## Objetivo de esta página

Esta página explica cómo se han integrado las soluciones de Trend dentro del código de la demo y cómo se conectan entre sí los distintos ficheros del proyecto.

El foco no está en Kubernetes ni en Helm por separado, sino en la arquitectura de software y en el recorrido real que sigue una petición a través del código fuente.

La idea es que esta página sirva como referencia didáctica para responder preguntas como:

- en qué fichero empieza todo
- qué funciones llaman a qué otras
- dónde se integra AI Guard
- dónde se integra File Security
- qué parte es UI, qué parte es backend y qué parte es seguridad
- qué piezas habría que tocar en un proyecto real de cliente

---

## Visión general de la arquitectura software

A nivel de software, la demo se divide en tres bloques:

1. Frontend
2. Backend
3. Servicios externos o auxiliares

### Frontend
Ubicación:
- `portal-frontend/src/`

Responsabilidad:
- mostrar la interfaz
- capturar acciones del usuario
- llamar al backend mediante `/api/...`

### Backend
Ubicación:
- `portal-backend/app/`

Responsabilidad:
- exponer endpoints
- coordinar lógica de negocio
- integrar AI Guard
- integrar File Security
- llamar al modelo LLM

### Servicios externos o auxiliares
Incluye:
- OpenAI
- Trend AI Guard
- Trend File Security contenerizado

---

## Mapa de ficheros clave

## Frontend

### `portal-frontend/src/App.jsx`
Es el centro funcional del frontend.

Aquí se implementan:

- el estado del chat
- el estado de subida de ficheros
- las llamadas a `/api/chat`
- las llamadas a `/api/files/upload`
- la actualización visual de resultados

### `portal-frontend/src/index.css`
Contiene estilos visuales.

### `portal-frontend/nginx.conf`
Define el proxy interno del frontend hacia el backend.

Es importante porque el frontend llama a rutas `/api/...` y Nginx las reenvía al servicio backend dentro de Kubernetes.

---

## Backend

### `portal-backend/main.py`
Punto de entrada de FastAPI.

Aquí se registran los routers principales.

Responsabilidad:
- arrancar la aplicación
- incluir los routers de chat, files y stats

### `portal-backend/app/routes/chat.py`
Expone el endpoint del chatbot.

Responsabilidad:
- recibir el mensaje del usuario
- coordinar la validación con AI Guard
- llamar al servicio de chatbot
- devolver la respuesta al frontend

### `portal-backend/app/routes/files.py`
Expone el endpoint de subida de archivos.

Responsabilidad:
- recibir el archivo
- delegar en la lógica de almacenamiento y análisis
- devolver el resultado al frontend

### `portal-backend/app/services/chatbot.py`
Encapsula la llamada al proveedor LLM.

Responsabilidad:
- construir el cliente OpenAI
- enviar el prompt
- devolver el texto generado

### `portal-backend/app/services/ai_guard.py`
Encapsula la llamada a Trend AI Guard.

Responsabilidad:
- construir la petición HTTP
- enviar el prompt o output a Trend
- interpretar la respuesta
- devolver una decisión normalizada al resto del backend

### `portal-backend/app/services/ai_events.py`
Registra eventos relacionados con la seguridad conversacional.

Responsabilidad:
- persistir contadores o eventos usados en la demo
- alimentar estadísticas del dashboard

### `portal-backend/app/services/file_security.py`
Encapsula la integración técnica con el scanner de File Security.

Responsabilidad:
- conectarse al scanner
- enviar el archivo
- devolver el resultado parseado

### `portal-backend/app/services/storage.py`
Define la lógica de negocio del flujo documental.

Responsabilidad:
- guardar el archivo
- llamar a File Security
- mover el fichero según veredicto
- devolver resultado normalizado al endpoint

### `portal-backend/app/services/stats.py`
Calcula las estadísticas mostradas en el panel.

Responsabilidad:
- contar ficheros por carpetas
- leer eventos de AI Guard
- devolver métricas consolidadas

---

## Cómo está desplegada la lógica de AI Guard en el código

## Punto de entrada

El flujo empieza en:

- `portal-backend/app/routes/chat.py`

Aquí se define el endpoint de chat, que recibe una petición JSON del frontend.

La responsabilidad de este fichero no es hablar directamente con OpenAI ni directamente con Trend, sino orquestar el flujo.

---

## Secuencia de llamadas en chat

### Paso 1. Llega una petición al endpoint
El endpoint recibe algo como:

- `message: "hola"`

### Paso 2. Se valida el prompt con AI Guard
`chat.py` llama a una función de `ai_guard.py`.

Conceptualmente, la secuencia es:

- route `/api/chat`
- `inspect_prompt(...)`
- `call_trend_ai_guard(...)`

### Paso 3. Si Trend bloquea, se corta el flujo
En ese caso:
- no se llama al modelo
- se genera una respuesta bloqueada
- se registra un evento en `ai_events.py`

### Paso 4. Si Trend permite, se llama al modelo
`chat.py` delega entonces en:

- `chatbot.py`
- función `get_ai_reply(...)`

### Paso 5. La salida del modelo vuelve a pasar por AI Guard
Después de la llamada al modelo, `chat.py` vuelve a usar `ai_guard.py` para evaluar la respuesta.

### Paso 6. Se devuelve la respuesta al frontend
Si la salida está permitida, el endpoint devuelve un JSON con `reply`.

---

## Qué hace exactamente `ai_guard.py`

Este fichero es el encapsulador de Trend AI Guard.

Responsabilidad principal:
- ocultar al resto del backend los detalles de la llamada HTTP a Trend

Eso significa que el resto del código no necesita saber:
- endpoint exacto
- cabeceras
- estructura de respuesta
- detalles de parsing

### Entrada del módulo
Recibe:
- texto
- dirección (`input` o `output`)

### Trabajo interno
1. Lee variables de entorno
2. Construye headers
3. Construye payload
4. Llama al endpoint de Trend
5. Interpreta si la acción es Allow o Block
6. Devuelve una estructura más simple

### Ventaja arquitectónica
La lógica de integración queda aislada en un solo fichero.

Si en un cliente cambiara:
- endpoint
- región
- esquema del payload
- formato de auditoría

la mayor parte del cambio quedaría concentrada aquí.

---

## Qué hace exactamente `chatbot.py`

Este fichero encapsula la llamada al modelo.

Responsabilidad principal:
- que el resto del backend no tenga que conocer el SDK del proveedor LLM

### Entrada del módulo
Recibe:
- el mensaje del usuario

### Trabajo interno
1. Lee `OPENAI_API_KEY`
2. Construye el cliente
3. Llama a `chat.completions.create(...)`
4. Extrae el texto final
5. Devuelve una cadena

### Ventaja arquitectónica
El acoplamiento con OpenAI queda aislado.

Si en un cliente se cambia a:
- Azure OpenAI
- otro proveedor
- un gateway corporativo
- un modelo local

el cambio principal debería concentrarse en este fichero.

---

## Cómo está desplegada la lógica de File Security en el código

## Punto de entrada

El flujo empieza en:

- `portal-backend/app/routes/files.py`

Este endpoint recibe un archivo del frontend mediante `multipart/form-data`.

Su responsabilidad no es hacer el análisis directamente, sino delegar.

---

## Secuencia de llamadas en files

### Paso 1. Llega un archivo al endpoint
El endpoint recibe el fichero.

### Paso 2. Se delega en la capa de almacenamiento
`files.py` llama a:

- `store_and_classify_file(...)`
- implementado en `storage.py`

### Paso 3. `storage.py` guarda el fichero
Primero se guarda físicamente en:

- `/data/uploads/incoming`

### Paso 4. `storage.py` llama a File Security
Después invoca:

- `scan_file(...)`
- implementado en `file_security.py`

### Paso 5. `file_security.py` habla con el scanner
Aquí se produce la llamada real al scanner gRPC de Trend.

### Paso 6. `storage.py` interpreta el resultado
Con el resultado del scanner decide:

- mover a clean
- mover a quarantine
- dejar en incoming

### Paso 7. El endpoint devuelve el resultado al frontend
`files.py` construye la respuesta JSON final con el veredicto y metadatos.

---

## Qué hace exactamente `storage.py`

Este fichero es clave porque traduce un resultado técnico en una decisión de negocio.

Responsabilidad principal:
- gobernar el ciclo de vida del fichero

### Trabajo interno
1. construir ruta de entrada
2. guardar fichero
3. llamar a `scan_file(...)`
4. inspeccionar veredicto
5. decidir carpeta destino
6. mover fichero
7. devolver resultado enriquecido

### Por qué esta separación es buena
Porque `storage.py` no necesita saber cómo funciona gRPC ni cómo habla Trend.

Solo necesita entender una salida normalizada:

- clean
- malicious
- error

Es decir:
- `file_security.py` resuelve el problema técnico
- `storage.py` resuelve el problema de negocio

---

## Qué hace exactamente `file_security.py`

Este fichero encapsula la integración con el scanner.

Responsabilidad principal:
- conectar con el host gRPC
- ejecutar el scan
- parsear la respuesta técnica

### Trabajo interno
1. leer `FILE_SECURITY_HOST`
2. leer `FILE_SECURITY_API_KEY`
3. abrir conexión al scanner
4. ejecutar el análisis del fichero
5. recibir respuesta raw
6. parsear y devolver estructura útil al backend

### Resultado que devuelve
Normalmente un diccionario con campos como:

- status
- scan_id
- malware_count
- file_type
- file_sha256
- scanner_version
- elapsed_time
- app_name
- data_source

### Ventaja arquitectónica
Igual que con AI Guard, el resto del backend no queda acoplado al detalle técnico del scanner.

Si en cliente cambiara:
- naming del service
- namespace
- release Helm
- forma de conectar con el scanner

el cambio estaría concentrado aquí y en configuración.

---

## Cómo se conectan frontend y backend

## Chat en frontend

En `App.jsx` existe una función que ejecuta:

- `fetch("/api/chat", ...)`

No habla con OpenAI, no habla con Trend, no contiene lógica de seguridad.

Solo:
- recoge input del usuario
- llama al backend
- pinta la respuesta

## Subida de ficheros en frontend

También en `App.jsx` existe la lógica que hace:

- `fetch("/api/files/upload", ...)`

De nuevo, no contiene lógica de seguridad.

El frontend se mantiene simple, y toda la lógica sensible vive en backend.

---

## Qué hace Nginx en el frontend

`portal-frontend/nginx.conf` define el puente entre la SPA y el backend.

Hay un bloque crítico:

- `location /api/`

Ese bloque reenvía las peticiones a:

- `backend-service:8007`

Esto permite que el frontend llame a `/api/...` sin tener que conocer detalles de cluster o puertos internos.

---

## Cómo se despliegan estas integraciones a nivel software

## AI Guard
No se despliega como componente propio en el cluster.

Se “despliega” en software de esta manera:

1. el backend incluye `ai_guard.py`
2. el deployment del backend inyecta:
   - TREND_API_KEY
   - TREND_AI_URL
   - TREND_AI_APP_NAME
3. las rutas del backend invocan ese servicio

Es decir:
AI Guard no vive en un pod local; vive como integración lógica dentro del backend.

---

## File Security
Sí se despliega como infraestructura real en Kubernetes.

A nivel software, el backend depende de:

- `file_security.py`
- `storage.py`

A nivel infraestructura, esa integración necesita:
- namespace `visionone-filesecurity`
- Helm release del scanner
- service DNS accesible desde el backend

Es decir:
la integración está repartida entre:
- software en backend
- infraestructura en Kubernetes

---

## Qué pasa cuando se rompe algo

## Caso 1. Falla AI Guard
Normalmente se verá en `chat.py` o `ai_guard.py`.

El backend seguirá recibiendo la petición, pero la integración con Trend responderá con error o con política inesperada.

## Caso 2. Falla OpenAI
Se verá en `chatbot.py`.

AI Guard puede seguir funcionando, pero la llamada al modelo dará error.

## Caso 3. Falla File Security
Se verá en `file_security.py` o en la conectividad con el scanner.

`storage.py` seguirá funcionando, pero el resultado de scan vendrá como error y el fichero no saldrá de incoming.

---

## Qué tocar en un cliente real

Si hubiera que reutilizar este patrón en cliente, normalmente se tocarían estas piezas:

### Para la parte conversacional
- `chatbot.py`
- `ai_guard.py`
- `chat.py`

### Para la parte documental
- `file_security.py`
- `storage.py`
- `files.py`

### Para despliegue
- `k8s/backend.yaml`
- `k8s/frontend.yaml`
- secrets
- Helm values o release naming del scanner

---

## Principio arquitectónico que sigue la demo

La idea central es separar claramente:

- entrada HTTP
- lógica de negocio
- integración con seguridad
- integración con proveedores externos

En la práctica eso significa:

### Rutas
Orquestan y validan flujo.

### Servicios
Encapsulan integraciones técnicas.

### Infraestructura
Expone dependencias externas al software.

Esa separación hace que la demo sea didáctica y, sobre todo, reutilizable.

---

## Idea clave final

Las soluciones de Trend no están “pegadas” de forma improvisada dentro del código.

Están integradas como módulos de servicio bien separados:

- AI Guard en `ai_guard.py`
- File Security en `file_security.py`
- lógica documental en `storage.py`
- orquestación conversacional en `chat.py`

Eso permite que la demo no solo funcione, sino que sirva como blueprint real para proyectos de cliente.