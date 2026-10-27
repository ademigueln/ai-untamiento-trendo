# Frontend de la demo

React y Vite; build servido por Nginx sin privilegios en el puerto interno 8080. El servicio Kubernetes mantiene puerto 80. `/api` se redirige al backend; para desarrollo Vite usa `127.0.0.1:8007`.

La interfaz se divide en `components/` (paneles), `hooks/` (chat, uploads y estadísticas), `services/api.js` y `data/demo.js` (contenido ficticio).

Consulta [el desarrollo del proyecto](../docs/development.md) para instalar, ejecutar y validar. El arranque completo sigue siendo `scripts/desplegar_demo_full_v2.sh` desde la raíz.
