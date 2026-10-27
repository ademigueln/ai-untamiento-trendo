# Arranque rápido del recorrido oficial

El recorrido soportado usa macOS, zsh, Python 3, Colima, Docker CLI, kubectl y Helm.

```sh
brew install colima docker kubectl helm python@3.11
git clone https://github.com/ademigueln/ai-untamiento-trendo.git
cd ai-untamiento-trendo
cp .env.demo.local.example .env.demo.local
```

Completa las credenciales de OpenAI y Trend en `.env.demo.local` antes de continuar.

```sh
./scripts/desplegar_demo_full_v2.sh --check
./scripts/desplegar_demo_full_v2.sh
```

El script inicia Colima si es necesario. Acceso por defecto: frontend en http://127.0.0.1:8081 y estadísticas en http://127.0.0.1:9000/api/stats. Logs en `.runtime/logs/`.

El arranque construye imágenes del código local y reutiliza las que ya coinciden con ese contenido. No publica imágenes. La comprobación final valida HTTP, sin enviar un mensaje de pago al LLM.

Para comprobar las integraciones, ejecuta los diagnósticos documentados en el [README](../../README.md). Estos sí hacen peticiones reales.

Para cerrar solo los accesos locales:

```sh
./scripts/parar_ports.sh
```

Para eliminar la demo, incluidos namespaces y PVC de documentos:

```sh
./scripts/apagar_demo_full.sh
```

Más detalles en [Operación de la demo](OPERACION_DEMO.md). Este documento remite al README para mantener una sola descripción del recorrido.
