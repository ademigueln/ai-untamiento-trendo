import { useEffect, useRef, useState } from "react";
import "./index.css";
import logo from "./assets/logo.png";

const API_BASE = "";

export default function App() {
  const fileInputRef = useRef(null);
  const chatHistoryRef = useRef(null);

  const initialAssistantMessage = {
    role: "assistant",
    content:
      "Soy el asistente virtual del AI-untamiento de Trendo. Puedo ayudarte con trámites, documentación, expedientes y orientación sobre servicios municipales.",
  };

  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [messages, setMessages] = useState([initialAssistantMessage]);

const [selectedFile, setSelectedFile] = useState(null);
const [uploadStatus, setUploadStatus] = useState("");
const [uploadLoading, setUploadLoading] = useState(false);
const [uploadResult, setUploadResult] = useState(null);
const [uploadStage, setUploadStage] = useState("idle");

const [stats, setStats] = useState({
  incoming_files: 0,
  clean_files: 0,
  quarantine_files: 0,
  blocked_ai_attempts_demo: 0,
  total_ai_events: 0,
  prompt_injection_blocked: 0,
  sensitive_data_request_blocked: 0,
  harmful_output_blocked: 0,
  portal_status: "Operativo",
});

  const notices = [
    "Sede electrónica disponible 24x7 para trámites y presentación de documentación.",
    "Nueva oficina virtual con asistente IA para consultas sobre trámites municipales.",
    "Canal seguro para adjuntar documentación asociada a expedientes activos.",
  ];

  const quickActions = [
    { title: "Cita previa", subtitle: "Atención presencial y oficinas municipales" },
    { title: "Padrón municipal", subtitle: "Volantes, certificados y cambio de domicilio" },
    { title: "Tributos y recibos", subtitle: "Consulta y pago de tasas e impuestos" },
    { title: "Carpeta ciudadana", subtitle: "Estado de expedientes y documentación" },
  ];

  const suggestedQuestions = [
    "Quiero empadronarme en el municipio",
    "¿Qué documentación necesito para una licencia de obra menor?",
    "¿Cómo adjunto un documento a un expediente ya abierto?",
    "¿Qué significa que un expediente esté pendiente de documentación?",
  ];

  const expedientes = [
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

  const securityPillars = [
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

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (!response.ok) {
          throw new Error("No se pudieron cargar estadísticas");
        }
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error("Error cargando stats:", error);
      }
    };

    loadStats();
  }, [uploadStatus]);

  const sendChatMessage = async (forcedMessage = null) => {
    const rawMessage = forcedMessage ?? chatInput;
    const trimmedMessage = rawMessage.trim();

    if (!trimmedMessage || chatLoading) {
      return;
    }

    const userMessage = {
      role: "user",
      content: trimmedMessage,
    };

    const thinkingMessage = {
      role: "assistant",
      content: "Pensando respuesta...",
      temporary: true,
    };

    setMessages((prev) => [...prev, userMessage, thinkingMessage]);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmedMessage }),
      });

      if (!response.ok) {
        throw new Error("El backend devolvió un error en /api/chat");
      }

      const data = await response.json();

setMessages((prev) => {
  const withoutTemporary = prev.filter((msg) => !msg.temporary);
  return [
    ...withoutTemporary,
    {
      role: "assistant",
      content: data.reply || "El backend no devolvió respuesta.",
      guard_action: data.guard_action || null,
      guard_reason: data.guard_reason || null,
      guard_source: data.guard_source || null,
    },
  ];
});
    } catch (error) {
      console.error("Error en chatbot:", error);

      setMessages((prev) => {
        const withoutTemporary = prev.filter((msg) => !msg.temporary);
        return [
          ...withoutTemporary,
          {
            role: "assistant",
            content: "No se ha podido conectar con el backend del chatbot.",
          },
        ];
      });
    } finally {
      setChatLoading(false);
    }
  };

  const handleChatKeyDown = async (event) => {
    if (event.key === "Enter") {
      await sendChatMessage();
    }
  };

  const handleSuggestedQuestion = async (question) => {
    await sendChatMessage(question);
  };

  const clearConversation = () => {
    setMessages([initialAssistantMessage]);
    setChatInput("");
  };

  const openFileSelector = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

const handleFileSelection = (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  setSelectedFile(file);
  setUploadResult(null);
  setUploadStage("selected");
  setUploadStatus(`Archivo seleccionado: ${file.name}`);
};

const uploadSelectedFile = async () => {
  if (!selectedFile) {
    setUploadStatus("Primero tienes que seleccionar un archivo.");
    return;
  }

  try {
    setUploadLoading(true);
    setUploadStage("uploading");

    const formData = new FormData();
    formData.append("file", selectedFile);

    const response = await fetch(`${API_BASE}/api/files/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("El backend devolvió un error en /api/files/upload");
    }

    const data = await response.json();

    setUploadResult(data);

    if (data.verdict === "clean") {
      setUploadStage("clean");
      setUploadStatus("Archivo validado correctamente y disponible en el expediente.");
    } else {
      setUploadStage("quarantine");
      setUploadStatus("Archivo bloqueado por política de seguridad.");
    }
  } catch (error) {
    console.error("Error en subida:", error);
    setUploadStage("idle");
    setUploadStatus("No se ha podido subir el archivo al backend.");
  } finally {
    setUploadLoading(false);
  }
};

  return (
    <div className="page">
      <div className="topbar">
        <div className="container topbar-inner">
          <div className="topbar-left">
            <span>Sede electrónica</span>
            <span>Tablón de anuncios</span>
            <span>Transparencia</span>
          </div>
          <div className="topbar-right">
            <span>Accesibilidad</span>
            <span>ES | EU</span>
          </div>
        </div>
      </div>

      <header className="site-header">
        <div className="container header-main">
          <div className="brand">
            <div className="crest crest-logo">
  <img src={logo} alt="AI-untamiento de Trendo" />
</div>

            <div className="brand-text">
              <div className="eyebrow">AI-untamiento de Trendo</div>
              <h1>Sede Electrónica del AI-untamiento de Trendo</h1>
              <p>Trámites, expedientes, documentación y atención digital a la ciudadanía</p>
            </div>
          </div>

          <div className="header-actions">
            <div className="session-box">Sesión demo: ciudadano@trendo.es</div>
            <button className="primary-btn">Acceder a mi carpeta ciudadana</button>
          </div>
        </div>

        <nav className="nav">
          <div className="container nav-inner">
            <a href="#">Inicio</a>
            <a href="#">Trámites</a>
            <a href="#">Mis expedientes</a>
            <a href="#">Documentación</a>
            <a href="#">Asistente virtual</a>
            <a href="#">Ayuda y soporte</a>
          </div>
        </nav>
      </header>

      <main className="container main-content">
        <section className="hero-grid">
          <div className="hero-panel">
            <div className="hero-badge">Sede electrónica oficial</div>
            <h2>Portal institucional con IA y canal seguro de documentación</h2>
            <p>
              La ciudadanía puede consultar expedientes, recibir ayuda contextual con el asistente IA
              y aportar documentación por un canal preparado para procesos de inspección y protección.
            </p>

            <div className="hero-buttons">
              <button className="light-btn">Iniciar trámite</button>
              <button className="ghost-btn">Ver servicios digitales</button>
            </div>
          </div>

       <div className="summary-card premium-summary-card">
  <div className="summary-top">
    <div>
      <div className="section-label">Estado operativo</div>
      <h3 className="summary-title">Panel de actividad y protección</h3>
      <p className="summary-subtitle">
        Indicadores en tiempo real del canal documental y del servicio digital.
      </p>
    </div>

    <div className="portal-status-badge">
      <span className="status-dot-live"></span>
      {stats.portal_status}
    </div>
  </div>

  <div className="premium-kpi-grid">
    <div className="premium-kpi-card kpi-clean">
      <div className="premium-kpi-icon">✓</div>
      <div className="premium-kpi-label">Ficheros limpios</div>
      <div className="premium-kpi-value">{stats.clean_files}</div>
      <div className="premium-kpi-help">Documentos validados y disponibles</div>
    </div>

    <div className="premium-kpi-card kpi-quarantine">
      <div className="premium-kpi-icon">!</div>
      <div className="premium-kpi-label">En cuarentena</div>
      <div className="premium-kpi-value">{stats.quarantine_files}</div>
      <div className="premium-kpi-help">Archivos retenidos por política</div>
    </div>

    <div className="premium-kpi-card kpi-pending">
      <div className="premium-kpi-icon">…</div>
      <div className="premium-kpi-label">Pendientes</div>
      <div className="premium-kpi-value">{stats.incoming_files}</div>
      <div className="premium-kpi-help">Elementos aún no finalizados</div>
    </div>

<div className="premium-kpi-card kpi-ai">
  <div className="premium-kpi-icon">AI</div>
  <div className="premium-kpi-label">Bloqueos IA</div>
  <div className="premium-kpi-value">{stats.blocked_ai_attempts_demo}</div>
  <div className="premium-kpi-help">Eventos bloqueados por Trend AI Guard</div>
</div>
  </div>
  <div className="ai-summary-strip">
  <div className="ai-summary-item">
    <span className="ai-summary-label">Eventos IA totales</span>
    <span className="ai-summary-value">{stats.total_ai_events}</span>
  </div>

  <div className="ai-summary-item">
    <span className="ai-summary-label">Prompt injections bloqueados</span>
    <span className="ai-summary-value">{stats.prompt_injection_blocked}</span>
  </div>

  <div className="ai-summary-item">
    <span className="ai-summary-label">Solicitudes sensibles bloqueadas</span>
    <span className="ai-summary-value">{stats.sensitive_data_request_blocked}</span>
  </div>

  <div className="ai-summary-item">
    <span className="ai-summary-label">Salidas dañinas bloqueadas</span>
    <span className="ai-summary-value">{stats.harmful_output_blocked}</span>
  </div>
</div>
</div>
        </section>

        <section className="focus-grid">
          <div className="card featured-chat-card">
            <div className="card-header">
              <div>
                <div className="section-label">Asistencia digital</div>
                <h3>Asistente virtual del ciudadano</h3>
              </div>
              <div className="chat-header-actions">
                <div className="tag tag-violet">IA conversacional</div>
                <button className="secondary-btn small-btn" onClick={clearConversation}>
                  Nueva conversación
                </button>
              </div>
            </div>

            <div className="chat-area">
              <div className="chat-history" ref={chatHistoryRef}>
{messages.map((message, index) => (
  <div
    key={`${message.role}-${index}`}
    className={`chat-message ${
      message.role === "user" ? "user-message" : "bot-message"
    } ${message.temporary ? "temporary-message" : ""}`}
  >
    <div className="chat-role">
      {message.role === "user" ? "Ciudadano" : "Asistente IA"}
    </div>

    <p>{message.content}</p>

    {message.role === "assistant" &&
      message.guard_action &&
      message.guard_action !== "allowed" && (
        <div className="chat-guard-alert">
          <strong>Trend AI Guard:</strong> {message.guard_reason || "Contenido bloqueado"}
        </div>
      )}

    {message.role === "assistant" &&
      message.guard_action === "allowed" &&
      message.guard_source === "trend_ai_guard" && (
        <div className="chat-guard-ok">
          Validado por Trend AI Guard
        </div>
      )}
  </div>
))}
              </div>

              <div className="suggested-questions">
                {suggestedQuestions.map((question) => (
                  <button
                    key={question}
                    className="suggestion-chip"
                    onClick={() => handleSuggestedQuestion(question)}
                    disabled={chatLoading}
                  >
                    {question}
                  </button>
                ))}
              </div>

              <div className="chat-input-row">
                <input
                  type="text"
                  placeholder="Escribe tu consulta al asistente municipal..."
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  onKeyDown={handleChatKeyDown}
                  disabled={chatLoading}
                />
                <button className="primary-btn" onClick={() => sendChatMessage()} disabled={chatLoading}>
                  {chatLoading ? "Enviando..." : "Enviar"}
                </button>
              </div>

              <div className="micro-copy">
                Asistente protegido con capacidades de seguridad TrendAI
              </div>
            </div>
          </div>

          <div className="card featured-upload-card">
            <div className="card-header">
              <div>
                <div className="section-label">Canal documental</div>
                <h3>Adjuntar documentación</h3>
              </div>
              <div className="tag tag-rose">Punto crítico</div>
            </div>

            <div className="upload-box large-upload-box">
              <div className="upload-icon">↑</div>
              <div className="upload-title">Subida segura de documentos</div>
              <p>
                Adjunta PDF, JPG, PNG, formularios firmados o justificantes asociados a tus
                expedientes municipales.
              </p>

              <input
                ref={fileInputRef}
                type="file"
                style={{ display: "none" }}
                onChange={handleFileSelection}
              />

<div className="upload-buttons">
  <button className="primary-btn" onClick={openFileSelector}>
    Seleccionar archivo
  </button>
  <button className="secondary-btn" onClick={uploadSelectedFile} disabled={uploadLoading}>
    {uploadLoading ? "Subiendo..." : "Vincular a expediente"}
  </button>
</div>

<div className="upload-result-box">
  {uploadResult && (
    <div
      className={`upload-badge ${
        uploadResult.verdict === "clean" ? "badge-clean" : "badge-blocked"
      }`}
    >
      {uploadResult.verdict === "clean" ? "✔ Archivo seguro" : "✖ Archivo bloqueado"}
    </div>
  )}

  <div className="micro-copy upload-status-copy">
    {uploadStatus || "Canal protegido con capacidades de seguridad TrendAI"}
  </div>
</div>

<div className="upload-pipeline">
  <div className={`pipeline-step ${uploadStage !== "idle" ? "step-active" : ""}`}>
    <div className="pipeline-icon">1</div>
    <div className="pipeline-text">
      <div className="pipeline-title">Carga</div>
      <div className="pipeline-subtitle">Selección del fichero</div>
    </div>
  </div>

  <div className="pipeline-line"></div>

  <div
    className={`pipeline-step ${
      uploadStage === "selected" || uploadStage === "uploading" || uploadStage === "clean" || uploadStage === "quarantine"
        ? "step-active"
        : ""
    }`}
  >
    <div className="pipeline-icon">2</div>
    <div className="pipeline-text">
      <div className="pipeline-title">Recepción</div>
      <div className="pipeline-subtitle">Entrada en canal documental</div>
    </div>
  </div>

  <div className="pipeline-line"></div>

  <div
    className={`pipeline-step ${
      uploadStage === "uploading" || uploadStage === "clean" || uploadStage === "quarantine"
        ? "step-active"
        : ""
    }`}
  >
    <div className="pipeline-icon">3</div>
    <div className="pipeline-text">
      <div className="pipeline-title">Análisis</div>
      <div className="pipeline-subtitle">Evaluación del archivo</div>
    </div>
  </div>

  <div className="pipeline-line"></div>

  <div
    className={`pipeline-step ${
      uploadStage === "clean" || uploadStage === "quarantine" ? "step-active" : ""
    } ${uploadStage === "clean" ? "step-clean" : ""} ${
      uploadStage === "quarantine" ? "step-blocked" : ""
    }`}
  >
    <div className="pipeline-icon">4</div>
    <div className="pipeline-text">
      <div className="pipeline-title">Resultado</div>
      <div className="pipeline-subtitle">
        {uploadStage === "clean"
          ? "Disponible"
          : uploadStage === "quarantine"
          ? "Cuarentena"
          : "Pendiente"}
      </div>
    </div>
  </div>
</div>

{uploadResult && (
  <div className="upload-details-card">
    <div className="upload-details-row">
      <span className="details-label">Archivo</span>
      <span className="details-value">{uploadResult.filename}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Veredicto</span>
      <span className="details-value">{uploadResult.verdict}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Destino final</span>
      <span className="details-value">{uploadResult.final_path}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Tipo de fichero</span>
      <span className="details-value">{uploadResult.file_type || "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Malware detectado</span>
      <span className="details-value">{uploadResult.malware_count ?? "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Scan ID</span>
      <span className="details-value">{uploadResult.scan_id || "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Versión scanner</span>
      <span className="details-value">{uploadResult.scanner_version || "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">SHA256</span>
      <span className="details-value details-break">{uploadResult.file_sha256 || "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Tiempo análisis</span>
      <span className="details-value">
        {uploadResult.elapsed_time ? `${uploadResult.elapsed_time} µs` : "N/D"}
      </span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Origen</span>
      <span className="details-value">{uploadResult.data_source || "N/D"}</span>
    </div>

    <div className="upload-details-row">
      <span className="details-label">Aplicación</span>
      <span className="details-value">{uploadResult.app_name || "N/D"}</span>
    </div>
  </div>
)}
            </div>
          </div>
        </section>

        <section className="content-grid lower-priority-grid">
          <div className="left-column">
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="section-label">Avisos municipales</div>
                  <h3>Información destacada</h3>
                </div>
              </div>

              <div className="stack">
                {notices.map((notice) => (
                  <div key={notice} className="notice-item">
                    {notice}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div>
                  <div className="section-label">Carpeta ciudadana</div>
                  <h3>Mis expedientes</h3>
                </div>
                <button className="secondary-btn">Nuevo trámite</button>
              </div>

              <div className="stack">
                {expedientes.map((item) => (
                  <div key={item.id} className="expediente-item">
                    <div className="expediente-main">
                      <div className="exp-id">{item.id}</div>
                      <div className="exp-title">{item.title}</div>
                      <div className="exp-meta">
                        Área: {item.area} · Última actualización: {item.updated}
                      </div>
                    </div>
                    <div className={`status-pill ${item.statusClass}`}>{item.status}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="right-column">
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="section-label">Accesos rápidos</div>
                  <h3>Servicios frecuentes</h3>
                </div>
              </div>

              <div className="stack">
                {quickActions.map((item) => (
                  <div key={item.title} className="quick-item">
                    <div className="quick-title">{item.title}</div>
                    <div className="quick-subtitle">{item.subtitle}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div>
                  <div className="section-label">Overlay de seguridad</div>
                  <h3>Capas de protección TrendAI</h3>
                </div>
              </div>

              <div className="stack">
                {securityPillars.map((pillar) => (
                  <div key={pillar.title} className="security-block">
                    <div className="security-title">{pillar.title}</div>
                    <div className="security-points">
                      {pillar.points.map((point) => (
                        <div key={point} className="security-point">
                          <span className="dot"></span>
                          <span>{point}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <div className="footer-title">AI-untamiento de Trendo</div>
            <p>
              Sede electrónica municipal para la gestión de trámites, expedientes y atención
              ciudadana.
            </p>
          </div>
          <div>
            <div className="footer-title">Enlaces</div>
            <ul>
              <li>Aviso legal</li>
              <li>Política de privacidad</li>
              <li>Accesibilidad</li>
            </ul>
          </div>
          <div>
            <div className="footer-title">Contacto</div>
            <ul>
              <li>Tel: 010</li>
              <li>soporte@trendo.es</li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}