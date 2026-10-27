import logo from "./assets/logo.png";
import ChatPanel from "./components/ChatPanel";
import UploadPanel from "./components/UploadPanel";
import StatsPanel from "./components/StatsPanel";
import { notices, quickActions, expedientes, securityPillars } from "./data/demo";
import { useStats } from "./hooks/useStats";

export default function App() {
  const { stats, statsError, refreshStats } = useStats();
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
            <div className="session-box">Demostración · datos ficticios</div>
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
            <div className="hero-badge">Sede electrónica de demostración</div>
            <h2>Portal institucional con IA y canal seguro de documentación</h2>
            <p>
              La ciudadanía puede consultar expedientes, recibir ayuda contextual con el asistente
              IA y aportar documentación por un canal preparado para procesos de inspección y
              protección.
            </p>

            <div className="hero-buttons">
              <button className="light-btn">Iniciar trámite</button>
              <button className="ghost-btn">Ver servicios digitales</button>
            </div>
          </div>

          <StatsPanel stats={stats} statsError={statsError} />
        </section>

        <section className="focus-grid">
          <ChatPanel onComplete={refreshStats} />
          <UploadPanel onComplete={refreshStats} />
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
                  <h3>Expedientes de ejemplo</h3>
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
