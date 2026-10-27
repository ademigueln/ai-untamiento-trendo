import { useRef, useState } from "react";
import { api } from "../services/api";

export function useUpload(onComplete) {
  const fileInputRef = useRef(null);
  const busy = useRef(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadStage, setUploadStage] = useState("idle");
  const handleFileSelection = (event) => {
    const file = event.target.files[0];
    if (!file || busy.current) return;
    setSelectedFile(file);
    setUploadResult(null);
    setUploadStage("selected");
    setUploadStatus(`Archivo seleccionado: ${file.name}`);
  };
  const uploadSelectedFile = async () => {
    if (!selectedFile || busy.current) return;
    busy.current = true;
    setUploadLoading(true);
    setUploadStage("uploading");
    setUploadResult(null);
    try {
      const body = new FormData();
      body.append("file", selectedFile);
      const data = await api("/api/files/upload", { method: "POST", body });
      setUploadResult(data);
      const stage =
        data.verdict === "clean" ? "clean" : data.verdict === "malicious" ? "quarantine" : "error";
      setUploadStage(stage);
      setUploadStatus(
        stage === "clean"
          ? "Archivo analizado y admitido en el canal documental de la demo."
          : stage === "quarantine"
            ? "Archivo retenido en cuarentena."
            : "Análisis no completado. El archivo queda pendiente y no ha sido admitido.",
      );
    } catch (error) {
      setUploadStage("error");
      setUploadStatus(error.message);
    } finally {
      busy.current = false;
      setUploadLoading(false);
      onComplete();
    }
  };
  return {
    fileInputRef,
    selectedFile,
    uploadStatus,
    uploadLoading,
    uploadResult,
    uploadStage,
    handleFileSelection,
    uploadSelectedFile,
    openFileSelector: () => fileInputRef.current?.click(),
  };
}
