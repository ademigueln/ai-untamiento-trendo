# Revisión del proyecto AI-untamiento de Trendo

Fecha: 26 de octubre de 2026. Revisión inicial del estado local, incluidos cambios sin confirmar en Git.

**Actualización posterior:** se han aplicado las correcciones y la limpieza alrededor de `scripts/desplegar_demo_full_v2.sh`. Consulta `../overview/OPERACION_DEMO.md` y `../development.md` para la estructura y comportamiento vigentes. Este documento conserva los hallazgos iniciales; ya no representa un listado de tareas abiertas. El movimiento global a `apps/` se ha descartado en favor de conservar rutas estables.

## Diagnóstico

Es una demo de seguridad aplicada a una sede electrónica municipal. Su valor está en mostrar tres controles: AI Guard para el chat, File Security para documentos y TMAS para análisis de repositorio, imágenes y modelos. La separación inicial entre rutas y servicios del backend es razonable. No necesita microservicios adicionales ni una plataforma más compleja.

Los problemas principales son la divergencia entre documentación y despliegue, algunos comportamientos inseguros ante errores y la mezcla de aplicación, laboratorios y archivos de operación. Mover carpetas por sí solo no resolvería estos problemas.

## Qué contiene y cómo funciona

- `portal-frontend/`: SPA de React y Vite, servida por Nginx en el contenedor. Chat, subida de documentos y estadísticas funcionan mediante llamadas a la API. Los expedientes, avisos y acciones rápidas incluyen datos estáticos de demostración; no hay un gestor de expedientes real. `App.jsx` concentra 791 líneas y `index.css`, 1.095.
- `portal-backend/`: FastAPI con tres grupos de rutas: `/api/chat`, `/api/files/upload` y `/api/stats`. No hay base de datos: los archivos van a disco, los eventos a JSON y las conversaciones a una lista global en memoria.
- Chat: inspección de entrada → selección de contexto mediante palabras clave en cuatro TXT → historial reciente → OpenAI con `gpt-4o-mini` → inspección de salida. Es recuperación documental simple, sin embeddings ni búsqueda vectorial.
- Documentos: guardar en `incoming/` → escáner gRPC de Trend → mover a `clean/` o `quarantine/`, o mantener en `incoming/` ante ciertos errores.
- `k8s/`: backend, frontend, servicios, PVC, ingress y plantillas/archivos de secretos. File Security se instala mediante Helm en otro namespace.
- `scripts/`: despliegue, apagado, actualización de tokens, diagnósticos y escaneo IA. El despliegue actual usa Colima y Kubernetes y consume imágenes publicadas; no construye el código local.
- `.github/workflows/`: escaneo TMAS de repositorio, imágenes publicadas y proveedor LLM. No se observa un pipeline que construya, pruebe y despliegue la misma revisión de código.
- `docs/` y `ai-untamiento-trendo.wiki/`: documentación con solapamiento de arquitectura, arranque y operación.
- `agentic_ollama.yaml`, `scan_config.yaml`, `ai-scanner/`, `PX/` y `Container Security/`: configuraciones y material complementario. Las configuraciones de Ollama apuntan a un modelo local diferente del proveedor del portal; conviene conservarlas como laboratorio separado.

## Prioridad 0: corregir comportamientos antes de limpiar

### 1. Aislar y acotar la memoria del chat

Evidencia: `app/services/memory.py` define una única lista global. `chatbot.py` consulta los últimos seis mensajes pero sigue añadiendo todos, sin límite. No hay identificador de conversación en `ChatRequest`.

Consecuencia: distintos usuarios pueden compartir contexto, el proceso acumula memoria y varias réplicas tendrían historiales distintos. Además, `chatbot.py` guarda la respuesta antes de que `routes/chat.py` inspeccione su salida: una respuesta bloqueada permanece disponible para la siguiente conversación. El botón de borrar del frontend solo limpia la pantalla.

Propuesta: para una demo sencilla, eliminar el historial del servidor o introducir sesiones explícitas con límite de mensajes, caducidad y borrado real. Persistir únicamente los mensajes admitidos por la política. Si se incorpora identidad, vincular y autorizar las sesiones por usuario; un identificador por sí solo no constituye autenticación.

Validación: dos sesiones no comparten contenido; una salida bloqueada no reaparece en contexto; borrar conversación borra también su historial; el almacenamiento tiene un límite.

### 2. No admitir archivos sin un resultado válido

Evidencia: `file_security.py` devuelve `status=raw_result` cuando falla el parseo JSON. `storage.py` solo trata explícitamente `status=error`; para el resto, un `result.atse` ausente deriva en `malwareCount=0` y clasificación limpia. Un objeto vacío también seguiría esa ruta.

Propuesta: validar estructura, tipos y estado de finalización del resultado. Solo una respuesta de análisis válida y explícitamente limpia debe mover el archivo a `clean/`; respuesta desconocida, incompleta o no interpretable debe dejarlo pendiente o en error. Cerrar el canal gRPC en `finally`.

Validación: respuestas vacías, texto no JSON, errores y resultados incompletos nunca se clasifican como limpios; un documento limpio y uno malicioso siguen sus rutas correctas.

### 3. Controlar nombres, tamaño y concurrencia de los uploads

Evidencia: `save_file_incoming()` concatena directamente el nombre recibido con el directorio y lee el archivo completo en memoria. No hay límite de tamaño explícito en la ruta. Los nombres repetidos comparten destino. La ruta es `async`, pero invoca escritura y escaneo síncronos.

Propuesta: guardar con UUID interno, mantener el nombre original solo como metadato, verificar confinamiento de la ruta y copiar por bloques con límite de tamaño. Ajustar también el límite de Nginx. Ejecutar trabajo bloqueante fuera del bucle asíncrono, por ejemplo mediante una ruta síncrona o un thread pool; introducir cola solo si se necesita procesado largo en segundo plano.

Validación: nombres con rutas y cargas repetidas no escapan del almacenamiento ni sobrescriben archivos; una carga grande recibe un error controlado y no bloquea las otras peticiones.

### 4. Hacer explícito cuándo está activa la protección

Evidencia: `inspect_prompt()` e `inspect_output()` permiten continuar cuando Trend no responde. `_classify_trend_result()` usa `Allow` si falta `action`. El backend devuelve siempre `portal_status="Operativo"`.

Propuesta: modo estricto por defecto para el recorrido protegido y, si la demo necesita continuidad sin Trend, un modo permisivo configurable y visible. Distinguir rechazo de seguridad, indisponibilidad y resultado inválido. Mostrar estado degradado en la interfaz. El parámetro `direction` no se envía en el payload actual de AI Guard: documentar ese comportamiento y validar el contrato antes de afirmar que hay políticas distintas por dirección.

### 5. Separar credenciales y datos del código y de las imágenes

Evidencia: `k8s/file-security-secrets.yaml` está registrado en Git y el script lo regenera con un token. El README dice que no se versiona, pero `.gitignore` no lo excluye. Existe `PX/API Keys.txt`; no se ha reproducido ni evaluado su contenido. El backend tiene un `.env` local y su `.dockerignore` no lo excluye; `COPY . .` puede incorporarlo a la imagen. También incorpora `uploads/`, con dos archivos registrados en Git.

Propuesta: sacar de seguimiento los secretos generados y usar plantillas sin credenciales. Excluir `.env*`, datos de usuario y archivos locales del contexto de construcción. Revisar privadamente el contenido y el historial para determinar si hubo exposición y, si se confirma, revocar las credenciales afectadas. Añadir `.gitignore` no elimina secretos ya registrados ni del historial.

## Prioridad 1: conseguir un arranque reproducible

1. **Una entrada de despliegue estable.** El README y el quickstart apuntan a `scripts/desplegar_demo_full.sh`, eliminado en el estado local; existe `desplegar_demo_full_v2.sh`, usado por el actualizador de tokens. Consolidar en un nombre estable y actualizar referencias. Documentar Colima, que el script exige, frente a los requisitos actuales centrados en Docker Desktop.
2. **Decidir qué recorridos se mantienen.** Recomiendo Kubernetes como recorrido oficial completo con File Security; desarrollo local como recorrido rápido con integraciones configurables. Mantener Compose solo si se repara y se comprueba: hoy publica `5173:5173`, pero la imagen del frontend escucha en 80; además Nginx resuelve `backend-service`, mientras Compose declara `backend`. El entorno de Vite tampoco tiene proxy `/api` configurado. No basta con cambiar un puerto.
3. **Relacionar código, imagen y escaneo.** Kubernetes usa imágenes `0.3.5`; el workflow de imágenes escanea backend `0.3.3` y frontend `0.1.3`. Construir desde la revisión que se valida, escanear esas imágenes y desplegar el mismo identificador inmutable. Hacer visible si el despliegue usa código local o una versión publicada.
4. **Una configuración común.** Centralizar rutas, modelo, timeouts y política de errores; derivar también la ruta de eventos de la configuración de datos. Actualmente los eventos usan `/data/uploads/ai_security_events.json`, mientras los archivos usan `UPLOAD_DIR`. Elegir una plantilla de secretos coherente; `secret.example.yaml` no representa los tres secretos de la plantilla actual.
5. **Comprobaciones de disponibilidad reales.** Añadir probes de vida/preparación y recursos de backend/frontend. El test de despliegue solo busca la palabra `reply`, que también aparece en respuestas bloqueadas o de error de configuración: no demuestra que OpenAI y Trend funcionen correctamente. Separar prueba básica sin coste de pruebas explícitas de las integraciones.
6. **Scripts portables y coherentes.** Los dos `arrancar_*.sh` contienen rutas antiguas de Downloads y terminan procesos por puerto con `kill -9`. Sustituirlas por rutas relativas al propio script y controlar únicamente los procesos iniciados por la demo. Reutilizar contexto Kubernetes, carga de configuración y validaciones en los scripts de operación.

## Limpieza: qué quitar y qué conservar

### Candidatos claros, después de una comprobación final de referencias

- `simulate_file_analysis()`: simulador heredado sin llamadas encontradas; el flujo real ya usa Trend.
- `portal-frontend/src/App.css`: no se importa; mezcla estilos de plantilla y añadidos del portal. Verificar visualmente y eliminar o rescatar solo las reglas necesarias al componente correspondiente.
- `src/assets/react.svg`, `src/assets/vite.svg`, `src/assets/hero.png` y `public/icons.svg`: sin referencias encontradas en el código inspeccionado. Conservar `logo.png` y `public/favicon.svg`, que sí se referencian.
- `scripts/Archive.zip`: contiene dos versiones de scripts y metadatos de macOS. Git debe conservar la historia; revisar antes cualquier diferencia útil y retirar el ZIP del árbol de trabajo del proyecto.
- `portal-backend/-`: directorio vacío, candidato a retirar tras verificar que no lo usa ninguna herramienta local.
- Logs, `.DS_Store` y cachés: residuos locales; mantenerlos fuera del repositorio. No es necesario borrar `node_modules/` ni `.venv/` para mejorar la estructura: son entornos locales ya ignorados.
- `portal-frontend/README.md`: reemplazar el contenido de plantilla por instrucciones breves específicas o remitir al documento de desarrollo común.
- `.gitignore`: eliminar la entrada repetida `claveApi.txt` y completar exclusiones de secretos, resultados de escaneo y datos reales.

### Elementos que requieren consolidación, no borrado automático

- **Wiki y docs:** elegir `docs/` como fuente canónica y publicar la wiki desde ella, o mantener una wiki independiente bien configurada. Git registra la wiki como gitlink (`160000`), pero falta el mapeo en `.gitmodules`: `git submodule status` falla. Un clon no tiene un mecanismo completo para recuperar ese contenido.
- **`overrides.yaml` y `Container Security/overrides.yaml`:** no asumir que son duplicados por el nombre. Identificar qué producto y recorrido usa cada uno, documentarlo y darles nombres específicos. El despliegue principal inspeccionado configura File Security mediante `--set`, sin consumir el overrides raíz.
- **Laboratorios Ollama y PX:** agrupar por producto y propósito, separando material ejecutable de credenciales locales. No eliminar configuraciones de pruebas que representan escenarios distintos.
- **`portal-backend/uploads/`:** contiene datos registrados, mientras el servicio usa `data/uploads` por defecto y `/data/uploads` en Kubernetes. Si son muestras deliberadas, moverlas a fixtures documentados; si son datos de operación, retirarlos del seguimiento.

## Estructura objetivo propuesta

Aplicar en dos pasos: primero estabilizar sin mover las aplicaciones; después, si sigue aportando claridad, renombrar y agrupar con actualización conjunta de referencias.

```text
README.md                        # propósito y un arranque oficial
apps/
  backend/                       # actual portal-backend
    main.py
    app/
      routes/
      services/
      core/config.py
      data/                      # contexto municipal de la demo
    tests/
  frontend/                      # actual portal-frontend
    src/
      components/                # ChatPanel, UploadPanel, StatsPanel, Layout
      hooks/                     # useChat, useUpload, useStats
      services/api.js
      data/demo.js               # expedientes y textos estáticos
      styles/
deploy/
  compose.yaml                   # solo si se mantiene y valida
  k8s/                           # aplicación y plantillas
  helm/                          # valores por integración/producto
security/
  ai-scanner/
  labs/ollama/
  container-security/
  px/
scripts/
  deploy.sh
  stop.sh
  update-tokens.sh
  doctor.sh                      # diagnósticos con subcomandos
  lib/                           # configuración y funciones compartidas
docs/
  architecture.md
  quickstart.md
  development.md
  operations.md
  security/
.github/workflows/
```

Los datos de ejecución y las credenciales quedan en volúmenes o rutas locales ignoradas. Al mover directorios deben actualizarse contextos Docker, scripts, workflows, rutas documentales y documentación en la misma entrega. No recomiendo renombrar todo antes de arreglar los recorridos actuales.

## Optimizaciones recomendadas

- **Frontend mantenible:** extraer los tres paneles y la capa de acceso a la API. Reducir estilos globales y consolidar reglas por componente después de comparar la interfaz. Corregir idioma HTML (`en` → `es`) y título de plantilla. Actualizar estadísticas tras un chat y un upload completados: hoy dependen de `uploadStatus`, por lo que un bloqueo de chat no dispara su actualización. Diferenciar datos estáticos y estado real, y mostrar fallos de carga en vez de aparentar normalidad.
- **Menor trabajo por petición:** cargar y cachear los cuatro documentos al iniciar, con ruta basada en el archivo del módulo. Reutilizar conexiones HTTP cuando proceda y cerrar recursos con garantías. Mantener las inspecciones de entrada y salida: reducir latencia no justifica eliminarlas.
- **Eventos consistentes:** sustituir la lectura/modificación/escritura completa del JSON por SQLite con transacciones para esta demo de una réplica. Hoy cada evento reescribe todo el historial y cada consulta vuelve a recorrerlo; escrituras concurrentes pueden perder eventos. Separar eventos y documentos en rutas de datos explícitas para simplificar persistencia y retención.
- **Métricas honestas:** `total_ai_events` cuenta eventos registrados al bloquear, no todas las interacciones con IA. Renombrarlo o registrar explícitamente los distintos resultados. Estado operativo y contadores no sustituyen comprobaciones de integración.
- **Registro útil y discreto:** sustituir `print` de prompts, respuestas y resultados completos por logs estructurados con identificador de petición, duración, veredicto y errores redactados. Limitar retención y evitar conservar contenido ciudadano innecesario.
- **Construcciones reproducibles:** fijar dependencias Python con un lock o versiones controladas, usar el lockfile npm mediante `npm ci`, y fijar versiones de imágenes base, chart Helm y herramientas de escaneo. Revisar la ejecución como usuario sin privilegios en los contenedores.
- **Pruebas del recorrido que importa:** cobertura de decisiones del guard, contrato del escáner, aislamiento/borrado de conversación y archivos, más una prueba de integración con dependencias simuladas. Añadir build y lint del frontend y validación del backend a CI.
- **Escaneo IA con alcance claro:** `ai-scanner/tmas-aiscan-llm-config.yaml` apunta directamente a OpenAI y replica solo parte del prompt. No atraviesa el backend, su contexto documental, su memoria ni AI Guard. Conservarlo como evaluación del modelo y añadir una evaluación separada del portal si se quiere demostrar protección integral. No se ha verificado el contrato vigente del CLI ni que el código de salida imponga el bloqueo por severidad que afirma el comentario del workflow.
- **Mantener simplicidad:** no introducir Redis, una base vectorial, un bus de eventos ni más servicios sin necesidad medida. SQLite y recuperación documental por palabras clave pueden ser suficientes para el objetivo actual.

## Orden de ejecución y aceptación

1. **Contención y corrección funcional:** archivos desconocidos nunca limpios; uploads confinados; memoria aislada y aprobada; secretos fuera de código e imágenes. Validar mediante pruebas con dependencias simuladas.
2. **Arranque reproducible:** una máquina nueva sigue el quickstart y obtiene una versión identificable; fallos de Trend se muestran como degradación o rechazo según política; imágenes escaneadas y desplegadas coinciden.
3. **Limpieza de bajo riesgo:** retirar código/activos sin referencias, archivos históricos y datos de operación; resolver wiki y documentación; comprobar que build, interfaz y recorridos siguen funcionando.
4. **Refactor y rendimiento:** dividir frontend, centralizar configuración y persistencia, medir latencia por etapa, concurrencia de uploads y consumo de memoria antes/después. Solo después valorar el movimiento completo a la estructura objetivo.

## Alcance y validación de esta revisión

Se inspeccionaron código, manifiestos, scripts, workflows, archivos de configuración seleccionados, documentación, referencias de activos y metadatos Git. No se ejecutaron despliegues, escáneres, llamadas a modelos ni operaciones sobre el clúster; no se consultaron valores de credenciales. Las incidencias de ejecución se deducen del código y deben confirmarse con pruebas controladas.

- `npm run lint`: correcto.
- Sintaxis Python mediante AST: 12 archivos correctos; sin importar módulos ni llamar a servicios.
- `git submodule status`: falla por ausencia del mapeo de la wiki en `.gitmodules`.
- No se ha ejecutado el build ni una batería funcional; no se ha medido rendimiento y no se atribuyen mejoras porcentuales.
- Hay modificaciones y archivos nuevos previos a esta revisión. No se han alterado código, configuración, secretos ni despliegues; se añade únicamente este informe.
