import { useUpload } from "../hooks/useUpload";

export default function UploadPanel({ onComplete }) {
  const {
    fileInputRef,
    selectedFile,
    uploadStatus,
    uploadLoading,
    uploadResult,
    uploadStage,
    handleFileSelection,
    uploadSelectedFile,
    openFileSelector,
  } = useUpload(onComplete);
  return (
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
          Adjunta PDF, JPG, PNG, formularios firmados o justificantes asociados a tus expedientes
          municipales.
        </p>

        <input
          ref={fileInputRef}
          type="file"
          disabled={uploadLoading}
          style={{ display: "none" }}
          onChange={handleFileSelection}
        />

        <div className="upload-buttons">
          <button className="primary-btn" onClick={openFileSelector} disabled={uploadLoading}>
            Seleccionar archivo
          </button>
          <button
            className="secondary-btn"
            onClick={uploadSelectedFile}
            disabled={uploadLoading || !selectedFile}
          >
            {uploadLoading ? "Subiendo..." : "Enviar a análisis"}
          </button>
        </div>

        <div className="upload-result-box">
          {uploadResult && (
            <div
              className={`upload-badge ${
                uploadResult.verdict === "clean"
                  ? "badge-clean"
                  : uploadResult.verdict === "malicious"
                    ? "badge-blocked"
                    : "badge-pending"
              }`}
            >
              {uploadResult.verdict === "clean"
                ? "Archivo admitido"
                : uploadResult.verdict === "malicious"
                  ? "Archivo en cuarentena"
                  : "Análisis pendiente"}
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
              uploadStage === "selected" ||
              uploadStage === "uploading" ||
              uploadStage === "clean" ||
              uploadStage === "quarantine"
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
              <span className="details-label">Zona documental</span>
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
              <span className="details-value details-break">
                {uploadResult.file_sha256 || "N/D"}
              </span>
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
  );
}
