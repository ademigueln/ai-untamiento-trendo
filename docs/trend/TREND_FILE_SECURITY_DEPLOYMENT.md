# File Security

El recorrido oficial instala el scanner contenerizado mediante Helm y conecta el backend por gRPC. El análisis se ejecuta dentro del entorno; el registro y los demás componentes conservan sus dependencias de servicio y conectividad.

## Configuración del despliegue

- Contexto: `colima`.
- Namespace: `visionone-filesecurity`.
- Release: `my-release`.
- Chart fijado: `1.6.3`, definido en `scripts/lib/demo-config.sh`.
- Valores: `k8s/file-security.values.yaml`.
- Host predeterminado: `my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051`.

El script genera el secreto de registro y conserva `device-token-secret` si ya existe. Un error al consultar ese secreto aborta el despliegue. Los reinicios forzados de registro y gestión solo se habilitan con `--repair-security`.

`FILE_SECURITY_API_KEY` y `FILE_SECURITY_HOST` se cargan desde `.env.demo.local`. El backend usa el SDK fijado en `requirements.lock`. La conexión local mantiene TLS desactivado por compatibilidad con esta instalación; otro entorno requiere configurar y validar su transporte.

## Flujo documental

1. El backend limita la carga y copia el archivo por bloques con un identificador interno único.
2. El adaptador inicializa el canal, solicita el análisis y lo cierra en `finally`.
3. El servicio valida el contrato del resultado y decide la zona documental.

Los destinos son `clean` para un análisis válido y limpio, `quarantine` para detección de malware e `incoming` para un error o un resultado desconocido. Un resultado incompleto no se interpreta como limpio.

El límite predeterminado es 20 MiB por archivo; Nginx permite un margen para la envoltura multipart. El nombre original se utiliza como dato de presentación, nunca como ruta de almacenamiento. La respuesta muestra el identificador, veredicto, zona y metadatos disponibles del análisis.

## Verificación

```sh
./scripts/troubleshooting_file_security.sh
```

La prueba utiliza EICAR y modifica los datos y contadores de la demo. Los diagnósticos comparten contexto, puertos y registro de procesos con el arranque oficial. Las pruebas automatizadas comprueban, sin contactar con Trend, la clasificación, el cierre del canal y el tratamiento de errores.
