# TMAS y validación continua

Los archivos de `.github/workflows/` separan validación funcional y análisis de seguridad. Se preparan localmente; su publicación y ejecución en GitHub son un paso independiente.

## Validación de la aplicación

`validate.yml` ejecuta pruebas Python, pruebas del despliegue con herramientas simuladas, comprobación de formato, lint y build del frontend. Utiliza los lockfiles del proyecto y no necesita credenciales de proveedores.

## Escaneo del repositorio

`tmas-repo-scan.yml` analiza el checkout con TMAS para buscar vulnerabilidades OSS y secretos. El análisis de malware no se activa para este artefacto de directorio.

## Escaneo de imágenes

`tmas-image-scan.yml` construye backend y frontend desde la revisión que se ejecuta, los etiqueta con su SHA y analiza esas mismas imágenes del daemon Docker. Activa análisis de vulnerabilidades, malware y secretos.

Este workflow no utiliza las etiquetas remotas antiguas y no publica las imágenes. El recorrido local de Colima utiliza igualmente sus Dockerfiles, aunque identifica las imágenes por la huella del contenido local.

## Evaluación directa del modelo

`tmas-ai-scanner.yml` utiliza `security/ai-scanner/tmas-aiscan-llm-config.yaml` y apunta al proveedor OpenAI. No atraviesa el backend, la memoria de sesiones ni AI Guard, y por tanto no equivale a probar la protección integral del portal.

El formato de configuración y la política de severidad deben validarse con el CLI antes de atribuir garantías al escaneo. Publicar un informe no configura por sí solo una regla de bloqueo de merge.

## Configuración de GitHub

Los escaneos utilizan `TMAS_API_KEY`; la evaluación del modelo también necesita `OPENAI_API_KEY`. La región configurada es `eu-central-1`. Las credenciales se proporcionan mediante GitHub Secrets, no mediante archivos versionados.

Los permisos de workflows, comentarios y reglas de merge se revisarán al publicar. Los comandos locales de [desarrollo y validación](../development.md) permiten comprobar las aplicaciones antes de ese paso.
