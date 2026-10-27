export default function StatsPanel({ stats, statsError }) {
  if (!stats)
    return (
      <div className="summary-card" role="status">
        {statsError || "Consultando el estado del portal…"}
      </div>
    );
  return (
    <div className="summary-card premium-summary-card">
      {statsError && <p role="alert">{statsError}</p>}
      <div className="summary-top">
        <div>
          <div className="section-label">Estado operativo</div>
          <h3 className="summary-title">Panel de actividad y protección</h3>
          <p className="summary-subtitle">
            Indicadores del canal documental y consultas del periodo retenido. El estado externo
            refleja comprobaciones recientes.
          </p>
        </div>

        <div
          className={`portal-status-badge ${statsError || stats.portal_status !== "Operativo" ? "status-unverified" : ""}`}
        >
          <span className="status-dot-live"></span>
          {statsError ? "Sin conexión" : stats.portal_status}
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
      <p className="micro-copy">
        Retención: {stats.event_retention_days} días. Política del chat:{" "}
        {stats.guard_policy === "strict" ? "estricta" : "permisiva"}.
      </p>
      <div className="ai-summary-strip">
        <div className="ai-summary-item">
          <span className="ai-summary-label">Consultas IA registradas</span>
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
  );
}
