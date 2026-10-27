# Presentación de la demo

AI-untamiento de Trendo simula una sede municipal para mostrar cómo integrar seguridad en un portal con IA y carga documental. La interfaz contiene expedientes y textos ficticios; no consulta sistemas administrativos reales.

## Componentes

- **Portal:** React y Nginx presentan el chat, las subidas y el panel de actividad.
- **Backend:** FastAPI coordina OpenAI, AI Guard y el scanner de archivos.
- **File Security:** analiza documentos mediante un servicio gRPC instalado en Kubernetes.
- **AI Guard:** inspecciona el mensaje del usuario y la respuesta del modelo antes de incorporarla al historial.
- **TMAS:** los workflows preparados analizan código, imágenes y, por separado, el modelo.

El recorrido completo utiliza Colima con Docker y Kubernetes. Las imágenes se construyen a partir del código local y se reutilizan cuando su contenido no cambia.

## Escenarios

### Documento limpio o malicioso

Seleccionar un archivo y enviarlo al análisis. El portal muestra si se admite, se retiene en cuarentena o queda pendiente porque el análisis no pudo completarse. Solo un resultado válido y limpio admite el documento.

El diagnóstico general permite usar una muestra EICAR. Es una prueba explícita de la integración real; modifica los contadores y el almacenamiento documental de la demo.

### Consulta al asistente

Enviar una consulta municipal y observar la inspección de entrada, la generación de respuesta y su inspección de salida. Un bloqueo de política se muestra como tal; una avería del servicio de protección se trata de forma diferente.

La política predeterminada es estricta. Las conversaciones están aisladas, tienen límite y caducidad, y solo conservan intercambios aprobados. El botón «Nueva conversación» borra también el historial del servidor.

### Seguridad durante el desarrollo

Mostrar los workflows de validación y TMAS: pruebas y construcción de la aplicación, análisis del repositorio y análisis de imágenes construidas desde la revisión. La evaluación directa de OpenAI es independiente y no atraviesa las protecciones del portal.

## Lectura del panel

Los contadores documentales reflejan las carpetas del volumen persistente. Los eventos IA contienen metadatos de las consultas registradas dentro del periodo retenido, sin texto ciudadano. El estado de los servicios refleja observaciones recientes; no constituye una comprobación continua de disponibilidad externa.

Consulta [Operación](OPERACION_DEMO.md) para levantar, diagnosticar y detener el entorno.
