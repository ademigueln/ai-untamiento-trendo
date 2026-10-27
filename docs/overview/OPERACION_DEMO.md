# Operación del recorrido oficial

## Entrada y dependencias

`./scripts/desplegar_demo_full_v2.sh` continúa siendo el comando habitual. La secuencia depende de `.env.demo.local`, `scripts/lib/`, las dos aplicaciones, sus Dockerfiles/lockfiles, los manifiestos de `k8s/` y el chart File Security 1.6.3.

El arranque valida antes de operar. `--check` termina tras comprobar configuración y herramientas, sin iniciar runtime ni contactar con proveedores. Los puertos locales deben ser distintos y estar entre 1 y 65535.

## Secuencia vigente

1. Valida variables y herramientas. Arranca Colima con Docker y Kubernetes si es necesario; fija el contexto `colima`.
2. Asegura namespaces y consulta si ya existe el token de dispositivo de File Security. Un error de consulta aborta.
3. Serializa secretos a JSON con permisos 0600 en `.runtime/secrets/`, sin interpolar valores dentro de YAML. No regenera ni escribe secretos versionados en `k8s/`.
4. Aplica los secretos e instala/actualiza el chart en la versión fijada. Recursos en `k8s/file-security.values.yaml`; `noProxy` incorpora la IP del API de Kubernetes.
5. Espera File Security. El arranque normal no fuerza reinicios de sus componentes. `--repair-security` habilita los reinicios de registro y gestión usados por el recorrido anterior.
6. Calcula la huella de los archivos usados por cada construcción. Construye con Docker solo si falta la imagen correspondiente y genera los manifiestos con esas etiquetas en `.runtime/manifests/`. `imagePullPolicy: Never` evita recurrir por accidente a una imagen remota.
7. Aplica PVC, configuración y manifiestos. Reinicia backend para recoger cambios de credenciales; frontend se actualiza cuando cambia su imagen. Espera los despliegues.
8. Comprueba el DNS del scanner configurado realmente en el backend.
9. Reinicia únicamente los port-forwards registrados por esta copia del proyecto. Guarda PID y argumentos en `.runtime/port-forwards.json`; comprueba identidad antes de terminar un proceso.
10. Verifica frontend, backend, estadísticas y estadísticas a través del proxy frontend. No manda un mensaje al modelo ni afirma que HTTP equivalga a protección externa validada.

El código local se construye ahora en cada cambio de contenido. Docker y Kubernetes de Colima con runtime Docker comparten imágenes, según la [documentación oficial de Colima](https://github.com/abiosoft/colima#kubernetes). No se ejecuta `docker push`.

## Estructura consolidada

Se mantienen `portal-backend/`, `portal-frontend/` y `k8s/`: moverlos añadiría cambios sin mejorar el recorrido. `scripts/lib/` concentra configuración, imágenes, generación de secretos, actualización del entorno y procesos. Las aplicaciones tienen sus propias pruebas. `security/` reúne evaluaciones y otros laboratorios.

Compose, scripts de arranque con rutas antiguas, ZIP con versiones previas, plantillas de secretos ya sustituidas y activos sin uso se han retirado del árbol publicable. Los originales quedan en `.local/archive/`. Los uploads versionados se preservan en `.local/legacy-uploads/`. Los archivos de `.env` activos se conservan en su lugar e ignorados por Git.

La wiki se ha convertido en documentación de referencia en `docs/reference/wiki/`; su repositorio original se conserva en `.local/wiki-repository/`. No se mantiene el gitlink incompleto. README y este documento son la fuente operativa; las páginas históricas pueden describir el comportamiento anterior.

## Migración de datos y credenciales

El PVC y sus zonas documentales se mantienen. El nuevo backend guarda SQLite bajo la misma raíz de datos por defecto; importa una sola vez metadatos recientes del JSON antiguo, sin copiar prompts. El JSON original no se borra. Los documentos nuevos usan un identificador interno y conservan su nombre original como dato de respuesta; no se renombran documentos existentes.

Los archivos antiguos de secretos, los overrides con bootstrap token y credenciales incrustadas en PX se han apartado en `.local/`. Se han retirado del seguimiento local de Git cuando estaban registrados. El responsable confirmó la rotación de las credenciales expuestas el 27 de octubre de 2026. Los originales se conservan en el archivo privado, excluido de Git. Por decisión expresa del responsable se conserva el historial de Git; esta limpieza afecta al árbol actual.

## Operaciones separadas

- `parar_ports.sh`: cierra solo los accesos que haya registrado esta versión; mantiene aplicaciones y datos.
- `apagar_demo_full.sh`: desinstala File Security y borra ambos namespaces y el PVC. No es una pausa con conservación de datos.
- `update_tokens_and_deploy.sh`: modifica el entorno mediante escritura atómica con permisos privados y serialización shell, sin pasar la clave como argumento de proceso; después usa el mismo arranque.
- `troubleshooting_*.sh`: utiliza configuración y contexto comunes y hace pruebas reales. El diagnóstico general sube EICAR. No imprime los valores de variables del backend.
- `run_ai_scanner.sh`: evaluación directa de OpenAI; sus resultados no atraviesan los guardrails del portal.

Los accesos de versiones anteriores, sin registro PID, no se terminan por coincidencia global. Si uno ocupa un puerto al migrar, el arranque falla indicando el log; debe cerrarse ese proceso antiguo de forma explícita.

## Validación y límites

`./scripts/validate.sh` cubre backend, despliegue simulado, lint y build. `scripts/tests/smoke_containers.py` prueba las imágenes reales en contenedores desechables sin claves y fuera de Kubernetes. El recorrido se ha comprobado también con `--check` usando la configuración local. Pasan 15 pruebas de backend y 11 de despliegue/helpers, lint sin advertencias, build y la prueba real de contenedores. Los manifiestos pasan una simulación de kubectl (`--dry-run=client`), sin aplicarlos.

La memoria de conversaciones es por proceso, limitada y temporal: conservar una réplica y un worker. El canal gRPC del scanner local conserva TLS desactivado por compatibilidad con la instalación actual; para otro entorno debe configurarse y validarse TLS. El [SDK oficial](https://pypi.org/project/visionone-filesecurity/) utilizado está fijado en el lockfile.

Los workflows locales ya validan aplicaciones y construyen/escanean la imagen de la revisión, en vez de analizar etiquetas remotas antiguas. Se han preparado como archivos: aún no se han publicado, ejecutado ni configurado reglas de merge en GitHub. El alcance del formato y política del AI Scanner se debe validar con su CLI antes de atribuirle garantías de bloqueo por severidad.
