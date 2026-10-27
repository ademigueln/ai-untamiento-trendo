# Integraciones y laboratorios de seguridad

El arranque oficial solo instala File Security mediante `k8s/file-security.values.yaml` y conecta AI Guard desde el backend.

- `ai-scanner/`: evaluación directa del proveedor OpenAI. No atraviesa las rutas, la memoria ni AI Guard del portal; sus resultados no equivalen a una evaluación integral de la aplicación. Se ejecuta con `scripts/run_ai_scanner.sh`. Resultados y binario descargado en `.runtime/ai-scanner/`. `--check` valida el esquema sin credenciales ni escaneo; el instalador fija TMAS 2.335.0 y comprueba sus checksums.
- `labs/ollama/`: escenarios de escaneo local de Qwen/Ollama. No participan en el arranque de Colima del portal.
- `container-security/values.example.yaml`: configuración de referencia sin bootstrap token. Las dos configuraciones originales están preservadas en `.local/container-security/`; no publicarlas con sus credenciales.
- `px/launch-script.sh`: recorrido independiente de una máquina Ubuntu, con instalación de Docker y despliegue de otro repositorio. Sus credenciales locales se cargan desde `.local/px.env`. No lo ejecuta el arranque municipal ni se ha ejecutado durante esta revisión.

El responsable confirmó la rotación de las credenciales expuestas el 27 de octubre de 2026. Los originales se conservan en el archivo privado y no forman parte de los archivos publicables. Retirarlos del árbol actual no borra sus versiones históricas.
