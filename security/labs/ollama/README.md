# Laboratorio Ollama

Este escenario es independiente del portal municipal y utiliza `qwen2.5:1.5b` en Ollama para el objetivo, el evaluador y el atacante.

Ejecuta el CLI desde este directorio para que `scan_config.yaml` encuentre `agentic_ollama.yaml`:

```sh
cd security/labs/ollama
tmas aiscan llm -c scan_config.yaml
```

Los informes `report.html` y `report.json` se generan aquí y están excluidos de Git. Pueden contener conversaciones de prueba. La configuración se conserva como laboratorio; valida su compatibilidad con la versión del CLI antes de iniciar una ejecución larga.
