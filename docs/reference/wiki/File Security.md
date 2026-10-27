> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# File Security

## Objetivo de esta página

Esta página explica cómo se ha integrado y desplegado Trend Vision One File Security en la demo.

El foco es práctico:

- dónde está el código
- cómo se llama al scanner
- cómo se despliega
- qué dependencias hay
- qué errores típicos aparecen

---

## Qué papel juega File Security en la demo

File Security protege el flujo documental.

Cada archivo que sube el usuario pasa por este flujo:

1. recepción en backend
2. almacenamiento temporal
3. análisis por scanner
4. decisión de negocio
5. movimiento del fichero según veredicto

La idea es que el usuario no suba directamente archivos a una zona “válida” de negocio. Siempre existe una fase de inspección previa.

---

## Dónde está implementado en código

Los ficheros clave son:

- portal-backend/app/routes/files.py
- portal-backend/app/services/storage.py
- portal-backend/app/services/file_security.py

### `files.py`
Expone el endpoint de subida:

- `/api/files/upload`

Este endpoint recibe el fichero y delega en la capa de almacenamiento/procesado.

### `storage.py`
Contiene la lógica de negocio del flujo documental:

- guardar fichero
- llamar al scanner
- interpretar resultado
- mover fichero a clean, quarantine o dejarlo en incoming

### `file_security.py`
Contiene la integración técnica con Trend File Security:

- conexión al scanner
- ejecución del análisis
- parseo de respuesta
- normalización del resultado

---

## Flujo completo de subida

## Paso 1. El frontend sube un archivo

El frontend envía un `multipart/form-data` al endpoint:

- `/api/files/upload`

## Paso 2. El backend guarda el archivo temporalmente

Primero el archivo se guarda en:

- `/data/uploads/incoming`

Este paso es importante porque el scanner trabaja sobre fichero real en disco.

## Paso 3. Se llama a `scan_file(file_path)`

La capa `storage.py` invoca la función `scan_file(...)` del servicio `file_security.py`.

## Paso 4. El backend se conecta al scanner

La conexión se realiza contra el servicio interno de Kubernetes:

- my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

## Paso 5. El scanner devuelve un resultado

El resultado técnico incluye típicamente:

- scanId
- malwareCount
- fileTypeName
- hashes
- scannerVersion
- dataSource
- appName

## Paso 6. El backend aplica lógica de negocio

Según el veredicto:

- clean -> mover a `/data/uploads/clean`
- malicious -> mover a `/data/uploads/quarantine`
- error -> dejar en `/data/uploads/incoming`

## Paso 7. Se devuelve respuesta al frontend

La respuesta final al frontend incluye datos útiles para la demo:

- filename
- verdict
- final_path
- scan_id
- scanner_version
- file_sha256
- file_type
- malware_count
- data_source
- app_name

---

## Conexión al scanner

La demo usa el scanner contenerizado de Trend, no una llamada REST cloud.

### Tipo de conexión
- gRPC

### Host esperado
- my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051

### Variables de entorno relevantes
En el backend se usan:

- FILE_SECURITY_API_KEY
- FILE_SECURITY_HOST

Estas variables llegan desde el secret `trendo-file-security` en el namespace `trendo-demo`.

---

## Qué ocurre dentro de `file_security.py`

La lógica de este fichero se puede resumir así:

1. leer `FILE_SECURITY_HOST`
2. inicializar cliente / canal
3. enviar fichero al scanner
4. recibir resultado raw
5. parsear respuesta
6. devolver estructura normalizada al resto del backend

Además, durante el desarrollo se añadieron logs útiles para troubleshooting:

- cuándo empieza el scan
- qué host se está usando
- cuál es el resultado raw
- qué error exacto se produce si falla gRPC

Esto ha sido muy útil para distinguir entre:

- problema de DNS
- scanner no desplegado
- onboarding incompleto
- API key inválida
- fallo real del scanner

---

## Despliegue de File Security

El scanner se despliega en Kubernetes en el namespace:

- visionone-filesecurity

### Método de despliegue
- Helm

### Release usado en la demo
- my-release

### Chart
- visionone-filesecurity/visionone-filesecurity

---

## Componentes desplegados

Los principales son:

- scanner
- management-service
- backend-communicator
- scan-cache

Cada uno cumple una función dentro del despliegue contenerizado.

### scanner
Es el servicio principal que expone el endpoint gRPC.

### backend-communicator
Participa en el onboarding / comunicación interna del sistema.

### management-service
Expone parte de la gestión interna del despliegue.

### scan-cache
Da soporte al funcionamiento del scanner.

---

## Secrets necesarios para File Security

En el namespace `visionone-filesecurity` se necesitan:

- token-secret
- device-token-secret

### `token-secret`
Contiene:
- registration-token

Este token es crítico para que el onboarding del scanner funcione.

### `device-token-secret`
Se utiliza durante el proceso de inicialización.

---

## Dependencia crítica: onboarding correcto

Durante el troubleshooting se vio que uno de los errores más frecuentes es que el chart se despliegue, pero el onboarding falle.

Síntomas típicos:

- `backend-communicator` en `Init:CrashLoopBackOff`
- `scanner` creado pero no ready
- logs del init container indicando problema de registration token

Conclusión práctica:
No basta con que exista el namespace o el service. Hay que confirmar que:

- el scanner está ready
- backend-communicator no está fallando
- el service del scanner existe
- el backend resuelve el DNS interno

---

## Validación técnica mínima

Para considerar File Security operativo, conviene validar al menos:

1. namespace existe
2. pods principales están `Running`
3. service del scanner existe
4. DNS resuelve desde el backend
5. subida de archivo devuelve resultado útil

Comandos típicos usados:

- `kubectl get pods -n visionone-filesecurity`
- `kubectl get svc -n visionone-filesecurity`
- `kubectl exec -n trendo-demo deployment/backend -- python ... socket.gethostbyname(...)`

---

## Errores típicos observados

## 1. DNS resolution failed
Causa:
- scanner no desplegado
- namespace inexistente
- service inexistente

Síntoma:
- error gRPC status code 14
- domain name not found

## 2. token-secret no encontrado
Causa:
- secret no creado en namespace correcto

Síntoma:
- init-token falla
- onboarding no puede continuar

## 3. registration token inválido
Causa:
- token erróneo o copiado de otra funcionalidad

Síntoma:
- backend-communicator en CrashLoop
- logs del onboarding con validation failed

## 4. FILE_SECURITY_HOST incorrecto
Causa:
- release name distinto
- nombre del service distinto
- valor antiguo persistido en secret de app

Síntoma:
- el backend intenta hablar contra un host inexistente

---

## Qué partes son reutilizables en cliente

El patrón general es totalmente reutilizable:

- carpeta incoming como staging
- análisis antes de admitir el fichero
- clasificación a clean/quarantine
- respuesta rica para UI o auditoría

Lo que normalmente cambiaría:

- tipo de almacenamiento
- naming de carpetas
- naming de namespace y release Helm
- tratamiento de errores
- integración con repositorio documental del cliente
- logging / SIEM / auditoría

---

## Idea clave

File Security no debe verse como una simple llamada técnica al scanner.

En realidad define un patrón documental seguro:

- nunca se acepta directamente un archivo como válido
- siempre existe una zona de inspección
- el backend actúa como orquestador
- el scanner actúa como control técnico de admisión

Ese patrón es precisamente lo reutilizable en cliente.