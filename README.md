# AI-untamiento de Trendo

Demo de sede municipal con React, FastAPI y OpenAI. Muestra protección del chat mediante AI Guard, inspección documental con File Security y análisis con TMAS. Los expedientes y el contenido institucional son ficticios.

## Arranque

```sh
./scripts/desplegar_demo_full_v2.sh
```

Usa Colima con Docker y Kubernetes. Construye las imágenes del código local si no existe una imagen para ese contenido. Las etiqueta con su huella, las reutiliza en siguientes arranques y no las publica en ningún registro. Docker y Kubernetes de Colima comparten imágenes.

Las imágenes antiguas de Docker Hub ya no son la fuente del recorrido local. Esto garantiza que los cambios del código llegan a la demo. La primera construcción necesita Internet; los siguientes arranques aprovechan la caché.

## Preparación

macOS, zsh, Python 3 y estas herramientas:

```sh
brew install colima docker kubectl helm python@3.11
cp .env.demo.local.example .env.demo.local
```

Completa en `.env.demo.local` las credenciales de OpenAI, AI Guard y File Security y conserva los puertos que quieras utilizar. `TMAS_API_KEY` es solo para el escaneo independiente.

```sh
# Valida configuración y herramientas, sin iniciar ni modificar el clúster
./scripts/desplegar_demo_full_v2.sh --check

# Arranca la demo
./scripts/desplegar_demo_full_v2.sh
```

Accesos por defecto:

- Frontend: http://127.0.0.1:8081
- Backend: http://127.0.0.1:9000
- Estadísticas: http://127.0.0.1:9000/api/stats

Si Colima está apagado, se inicia con 4 CPU, 8 GB de RAM y Kubernetes. Todas las operaciones del recorrido apuntan al contexto `colima`.

## Organización

```text
portal-backend/                 FastAPI, configuración central y pruebas
portal-frontend/                React: paneles, hooks, API y datos de ejemplo
k8s/                           Manifiestos, configuración y valores de File Security
scripts/
  desplegar_demo_full_v2.sh     Entrada oficial
  apagar_demo_full.sh           Eliminación completa del despliegue
  parar_ports.sh               Cierre de accesos locales registrados
  update_tokens_and_deploy.sh   Actualización de tokens y despliegue
  troubleshooting_*.sh         Pruebas con integraciones reales
  dev_backend.sh               Desarrollo local, puerto 8007
  dev_frontend.sh              Desarrollo local con Vite
  validate.sh                  Pruebas, lint y build
  lib/                         Configuración, imágenes, secretos y procesos
  tests/                       Pruebas aisladas del despliegue y contenedores
security/
  ai-scanner/                  Evaluación directa del modelo OpenAI
  labs/ollama/                 Laboratorio independiente de Ollama
  container-security/          Referencia sin token de bootstrap
  px/                          Recorrido Ubuntu independiente, sin claves incrustadas
docs/
  overview/                    Operación canónica
  trend/                       Integraciones
  reference/wiki/              Wiki recuperada como documentación histórica
.runtime/                      Imágenes, manifiestos generados, logs, PID y entornos
.local/                        Archivo privado de originales y credenciales antiguas
```

`.runtime/` y `.local/` están ignorados por Git. Los secretos generados tienen permisos 0600 y se guardan en `.runtime/secrets/`. Los documentos siguen en el PVC y sus carpetas `incoming/`, `clean/` y `quarantine/`.

## Funcionamiento

- Conversaciones separadas por token aleatorio, con caducidad de 30 minutos, seis mensajes de contexto y capacidad máxima de 500 sesiones. Se conservan solo intercambios aprobados. «Nueva conversación» borra también el historial del servidor.
- AI Guard falla en modo estricto por defecto: un error o resultado desconocido no autoriza la petición. `GUARD_FAIL_OPEN` en `k8s/config.yaml` permite una demo permisiva explícita y visible, sin incorporar respuestas no verificadas al historial.
- Archivos con identificadores internos únicos, copia por bloques y límite de 20 MiB. Un análisis desconocido queda pendiente y nunca se admite como limpio. Los escaneos no bloquean el bucle asíncrono del servidor.
- Eventos en SQLite, sin texto de consultas, con retención de siete días y hasta 10.000 registros. Los metadatos recientes del JSON antiguo se importan una sola vez, sin copiar prompts ni borrar el original.
- El panel distingue servicios sin verificar, operativos y degradados según observaciones recientes. Actualiza tras chat/subidas y cada 30 segundos. No consume llamadas externas para mantener un indicador verde.
- Contenedores sin usuario root, imágenes base fijadas por digest, dependencias fijadas, probes y límites de recursos.

La memoria de chat es intencionadamente efímera y de una sola réplica: se pierde al reiniciar y no reemplaza autenticación de usuarios. No debe aumentarse el número de réplicas sin cambiar el almacenamiento de sesiones.

## Operación y diagnóstico

```sh
./scripts/parar_ports.sh
./scripts/update_tokens_and_deploy.sh
./scripts/troubleshooting_demo.sh
./scripts/troubleshooting_ai_guard.sh
./scripts/troubleshooting_file_security.sh
```

Los diagnósticos hacen llamadas reales; el general sube una muestra EICAR. El arranque solo comprueba HTTP y readiness, sin enviar mensajes de pago al LLM. Los port-forwards se registran y se detienen por PID validado, sin buscar procesos globalmente por nombre.

Para reparar componentes de registro de File Security de forma explícita:

```sh
./scripts/desplegar_demo_full_v2.sh --repair-security
```

El arranque normal conserva su registro y evita reinicios forzados de esos componentes. Usa el chart 1.6.3, la versión instalada al revisar la demo.

**Apagado completo:** `./scripts/apagar_demo_full.sh` desinstala File Security y elimina los dos namespaces y el PVC documental. Para conservar el despliegue y los datos, cierra solo los puertos. El apagado completo no detiene Colima ni borra las credenciales locales.

Logs en `.runtime/logs/`, versiones de imágenes en `.runtime/images.json` y manifiestos preparados en `.runtime/manifests/`.

## Validación y documentación

Prepara el entorno según [Desarrollo](docs/development.md) y ejecuta:

```sh
./scripts/validate.sh
```

Para comprobar las imágenes ya construidas, sin credenciales ni cambios en Kubernetes:

```sh
DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" python3 scripts/tests/smoke_containers.py
```

[Índice de documentación](docs/README.md) · [Operación y decisiones](docs/overview/OPERACION_DEMO.md) · [Integraciones independientes](security/README.md) · [Revisión inicial e incidencias corregidas](docs/reference/REVISION_INICIAL_2026-10-26.md).

Las credenciales retiradas y los originales están conservados en `.local/`. Se han sacado del seguimiento de Git los secretos antiguos, datos de usuario, overrides con token y el gitlink incompleto de la wiki. El responsable confirmó la rotación de las credenciales expuestas el 27 de octubre de 2026. Los originales privados siguen excluidos de Git; la retirada de archivos no elimina sus versiones históricas.
