export const notices = [
  "Sede electrónica disponible 24x7 para trámites y presentación de documentación.",
  "Nueva oficina virtual con asistente IA para consultas sobre trámites municipales.",
  "Canal seguro para adjuntar documentación asociada a expedientes activos.",
];

export const quickActions = [
  { title: "Cita previa", subtitle: "Atención presencial y oficinas municipales" },
  { title: "Padrón municipal", subtitle: "Volantes, certificados y cambio de domicilio" },
  { title: "Tributos y recibos", subtitle: "Consulta y pago de tasas e impuestos" },
  { title: "Carpeta ciudadana", subtitle: "Estado de expedientes y documentación" },
];

export const suggestedQuestions = [
  "Quiero empadronarme en el municipio",
  "¿Qué documentación necesito para una licencia de obra menor?",
  "¿Cómo adjunto un documento a un expediente ya abierto?",
  "¿Qué significa que un expediente esté pendiente de documentación?",
];

export const expedientes = [
  {
    id: "EXP-2026-00142",
    title: "Licencia de obra menor",
    area: "Urbanismo",
    status: "En revisión",
    updated: "18/03/2026",
    statusClass: "status-review",
  },
  {
    id: "EXP-2026-00417",
    title: "Solicitud de ayuda energética",
    area: "Servicios Sociales",
    status: "Pendiente de documentación",
    updated: "16/03/2026",
    statusClass: "status-pending",
  },
  {
    id: "EXP-2026-00608",
    title: "Alta en padrón municipal",
    area: "Atención al Ciudadano",
    status: "Resuelto",
    updated: "11/03/2026",
    statusClass: "status-done",
  },
];

export const securityPillars = [
  {
    title: "Protección del chatbot IA",
    points: [
      "Evaluación del flujo de la aplicación y del modelo utilizado.",
      "Mapeo de exposición frente a OWASP Top 10 for LLM Applications.",
      "Visibilidad alineada con MITRE ATLAS.",
    ],
  },
  {
    title: "Guardrails y control de respuestas",
    points: [
      "Bloqueo de prompt injection y manipulación del contexto.",
      "Controles sobre fuga de información sensible.",
      "Políticas de contenido y validación de entradas y salidas.",
    ],
  },
  {
    title: "Inspección de archivos",
    points: [
      "Análisis de documentos subidos por la ciudadanía.",
      "Bloqueo de malware y contenido malicioso.",
      "Punto ideal de integración para File Security.",
    ],
  },
];
