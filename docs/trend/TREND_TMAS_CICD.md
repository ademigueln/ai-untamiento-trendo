# TMAS y validación continua

Los archivos de `.github/workflows/` separan validación funcional y análisis de seguridad. Se preparan localmente; su publicación y ejecución en GitHub son un paso independiente.

## Validación de la aplicación

`validate.yml` ejecuta pruebas Python, pruebas del despliegue con herramientas simuladas, comprobación de formato, lint y build del frontend. También valida el esquema de AI Scanner con el CLI real, sin iniciar un escaneo ni necesitar credenciales. Utiliza los lockfiles del proyecto.

## Escaneo del repositorio

`tmas-repo-scan.yml` analiza el checkout con TMAS para buscar vulnerabilidades OSS y secretos. El análisis de malware no se activa para este artefacto de directorio.

## Escaneo de imágenes

`tmas-image-scan.yml` construye backend y frontend desde la revisión que se ejecuta, los etiqueta con su SHA y analiza esas mismas imágenes del daemon Docker. Activa análisis de vulnerabilidades, malware y secretos.

Este workflow no utiliza las etiquetas remotas antiguas y no publica las imágenes. El recorrido local de Colima utiliza igualmente sus Dockerfiles, aunque identifica las imágenes por la huella del contenido local.

## Evaluación directa del modelo

`tmas-ai-scanner.yml` utiliza `security/ai-scanner/tmas-aiscan-llm-config.yaml` y apunta al proveedor OpenAI. No atraviesa el backend, la memoria de sesiones ni AI Guard, y por tanto no equivale a probar la protección integral del portal.

El CLI se fija en **2.335.0** y sus descargas se verifican mediante los SHA-256 de `security/ai-scanner/tmas-cli.json`. El esquema de configuración validado es **2.16.0**; es una versión distinta de la del ejecutable.

```sh
./scripts/run_ai_scanner.sh --check  # Solo esquema, sin credenciales ni llamadas al modelo
./scripts/run_ai_scanner.sh          # Escaneo real
```

La configuración usa `target.api_key_env`, `target.openai.model`, `target.openai.system_prompt`, `attack_preset` y destinos `output`. Los informes se escriben en un subdirectorio nuevo de `.runtime/ai-scanner/results/` y se suben como artefactos. El preset OWASP utiliza dos tareas concurrentes y un límite de diez minutos. No se guardan transcripciones en los destinos de resultados.

El workflow valida primero el esquema y después comprueba que existan `TMAS_API_KEY` y `OPENAI_API_KEY`, sin imprimir sus valores. `TARGET_API_KEY` recibe el segundo secreto. Un secreto ausente provoca un error explícito antes de llamar al modelo; no se omite silenciosamente el escaneo. Los PR de forks solo cuentan con la validación sin secretos del workflow general.

El resultado no configura por sí solo una regla de bloqueo de merge. La política de severidad y los permisos reales de las claves se deben revisar por separado.

## Configuración de GitHub

Los escaneos utilizan `TMAS_API_KEY`; la evaluación del modelo también necesita `OPENAI_API_KEY`. La región configurada es `eu-central-1`. Las credenciales se proporcionan mediante GitHub Secrets, no mediante archivos versionados.

Los permisos de workflows, comentarios y reglas de merge se revisarán al publicar. Los comandos locales de [desarrollo y validación](../development.md) permiten comprobar las aplicaciones antes de ese paso.

## Referencia del contrato

La [referencia oficial de configuración](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-config-custom-ai-app-scan) describe los proveedores, las variables de entorno y los destinos de informes. La validación local se realiza con `tmas aiscan llm config validate`, sin `--strict-connectivity`.
