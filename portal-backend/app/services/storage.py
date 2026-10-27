import logging
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.services.file_security import scan_file
from app.services.ai_events import set_service_health

logger = logging.getLogger(__name__)


def classify_result(scan_result) -> str:
    if not isinstance(scan_result, dict) or scan_result.get("status") not in (None, "ok"):
        return "error"
    result = scan_result.get("result")
    atse = result.get("atse") if isinstance(result, dict) else None
    if not isinstance(atse, dict) or atse.get("error"):
        return "error"
    count = atse.get("malwareCount")
    if type(count) is not int or count < 0:
        return "error"
    if count > 0:
        return "malicious"
    if atse.get("malware"):
        return "error"  # Resultado contradictorio, no aceptarlo como limpio.
    return "clean"


def save_file_incoming(upload_file: UploadFile) -> Path:
    for folder in ("incoming", "clean", "quarantine"):
        (settings.upload_dir / folder).mkdir(parents=True, exist_ok=True)
    # Nombre generado; el nombre aportado nunca se utiliza como ruta.
    path = settings.upload_dir / "incoming" / uuid4().hex
    size = 0
    try:
        with path.open("xb") as destination:
            while chunk := upload_file.file.read(64 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, "El archivo supera el límite de tamaño permitido.")
                destination.write(chunk)
        if size == 0:
            raise HTTPException(400, "El archivo está vacío.")
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def store_and_classify_file(upload_file: UploadFile) -> dict:
    incoming = save_file_incoming(upload_file)
    raw = scan_file(str(incoming))
    result = raw if isinstance(raw, dict) else {"status": "error"}
    verdict = classify_result(result)
    set_service_health("file_security", verdict != "error")
    folder = {"clean": "clean", "malicious": "quarantine", "error": "incoming"}[verdict]
    destination = settings.upload_dir / folder / incoming.name
    if verdict != "error":
        incoming.rename(destination)
    logger.info("file_scan_completed verdict=%s file_id=%s", verdict, incoming.name)
    atse = result.get("result", {}).get("atse", {}) if isinstance(result.get("result"), dict) else {}
    atse = atse if isinstance(atse, dict) else {}
    return {
        "filename": (upload_file.filename or "documento").replace("\\", "/").rsplit("/", 1)[-1][:255],
        "file_id": incoming.name, "verdict": verdict, "final_path": folder,
        "scan_id": result.get("scanId"), "scanner_version": result.get("scannerVersion"),
        "file_sha256": result.get("fileSHA256"), "file_type": atse.get("fileTypeName"),
        "malware_count": atse.get("malwareCount"), "elapsed_time": atse.get("elapsedTime"),
        "data_source": result.get("dataSource"), "app_name": result.get("appName"),
        "scan_error": "Análisis no completado; archivo pendiente." if verdict == "error" else None,
    }
