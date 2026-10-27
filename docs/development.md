# Desarrollo y comprobaciones

## Entorno Python

Usa Python 3.11, la misma rama que la imagen de backend y CI:

```sh
python3.11 -m venv .runtime/test-venv
.runtime/test-venv/bin/python -m pip install -r portal-backend/requirements.lock
cd portal-frontend
npm ci
cd ..
```

`requirements.txt` fija dependencias directas; `requirements.lock` fija también las transitivas que se han construido y probado. Al actualizar dependencias, recrear el entorno, resolver, revisar el lock y volver a ejecutar todas las pruebas. Las bases de Docker se fijan por digest: actualizar sus etiquetas sin cambiar el digest no cambia la imagen.

## Validación sin proveedores

```sh
./scripts/validate.sh
```

Incluye pruebas del chat, guardrails, almacenamiento, SQLite y despliegue con herramientas simuladas; comprobación de formato, lint con cero advertencias y build del frontend. Las credenciales son ficticias y las rutas temporales. La prueba de contenedores es explícita y separada porque requiere Docker:

```sh
DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" python3 scripts/lib/build-images.py "$PWD"
DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" python3 scripts/tests/smoke_containers.py
```

La segunda crea una red y dos contenedores temporales sin claves, comprueba usuarios sin privilegios, frontend, proxy API, preparación y escritura de datos; los elimina al terminar. No comparte el PVC de Kubernetes.

## Iteración rápida

En dos terminales:

```sh
./scripts/dev_backend.sh
./scripts/dev_frontend.sh
```

Vite redirige `/api` al backend local en 8007. El backend usa datos separados en `.runtime/dev/`. Para las integraciones reales, el host del scanner configurado debe ser accesible desde la máquina local; el DNS interno de Kubernetes no lo es por defecto. Para demostrar la integración completa, usa el arranque oficial de Colima.

## Contratos y límites

- POST `/api/chat`: `message` de 1 a 8.000 caracteres y `conversation_id` opcional. La primera respuesta devuelve un token aleatorio; enviarlo en la siguiente consulta. Un token caducado devuelve 404, uno ocupado 409, y un proveedor indisponible 503. Un bloqueo de política es una respuesta controlada, distinta de una avería.
- DELETE `/api/chat/{token}`: borra el historial; 204 incluso si ya no existe. El token permite acceso a esa conversación de demo: no compartirlo ni registrarlo. No es autenticación ciudadana.
- POST `/api/files/upload`: archivo máximo de 20 MiB, nombre interno aleatorio, error de tamaño 413. Respuesta `clean`, `malicious` o `error`; `error` conserva el documento pendiente. No interpreta una avería del escáner como malware ni como limpieza.
- GET `/api/stats`: conteos documentales, consultas registradas en el intervalo retenido, política y última observación de servicios (caduca a los cinco minutos). Los eventos importados son solo los bloqueos que registraba el formato antiguo.
- `/health/live`: vida del proceso. `/health/ready`: almacenamiento y base de eventos accesibles. No garantiza credenciales válidas ni disponibilidad de proveedores.

No hay nuevas sesiones persistentes, base vectorial ni servicios de cola. SQLite y una réplica bastan para el objetivo de esta demo.

## Estilo del frontend

```sh
npm run format --prefix portal-frontend
npm run format:check --prefix portal-frontend
```

El formato se define en `portal-frontend/.prettierrc.json` y se comprueba en CI. Los archivos históricos de referencia se conservan sin reformatearlos.
