import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.services.file_security import scan_file

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))

INCOMING_DIR = UPLOAD_DIR / "incoming"
CLEAN_DIR = UPLOAD_DIR / "clean"
QUARANTINE_DIR = UPLOAD_DIR / "quarantine"


def ensure_directories():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)


def save_file_incoming(upload_file: UploadFile) -> Path:
    ensure_directories()

    file_path = INCOMING_DIR / upload_file.filename

    with open(file_path, "wb") as f:
        content = upload_file.file.read()
        f.write(content)

    return file_path


def simulate_file_analysis(filename: str) -> str:
    suspicious_words = ["virus", "malware", "bad"]

    lower_name = filename.lower()

    for word in suspicious_words:
        if word in lower_name:
            return "quarantine"

    return "clean"


def move_file_to_final_location(source_path: Path, verdict: str) -> Path:
    if verdict == "clean":
        destination = CLEAN_DIR / source_path.name
    else:
        destination = QUARANTINE_DIR / source_path.name

    shutil.move(str(source_path), str(destination))
    return destination


def store_and_classify_file(upload_file: UploadFile) -> dict:
    print(f"[STORAGE] Procesando fichero: {upload_file.filename}")

    incoming_path = save_file_incoming(upload_file)
    print(f"[STORAGE] Guardado en incoming: {incoming_path}")

    scan_result = scan_file(str(incoming_path))
    print(f"[STORAGE] Resultado scan_file(): {scan_result}")

    if scan_result.get("status") == "error":
        verdict = "error"
        final_path = incoming_path
        print("[STORAGE] Veredicto = error, el fichero se queda en incoming")
    else:
        atse_result = scan_result.get("result", {}).get("atse", {})
        malware_count = atse_result.get("malwareCount", 0)
        malware_info = atse_result.get("malware")
        scan_error = atse_result.get("error")

        if scan_error:
            verdict = "error"
            final_path = incoming_path
            print(f"[STORAGE] Error reportado por scanner: {scan_error}")
        elif malware_count and malware_count > 0:
            verdict = "malicious"
            final_path = move_file_to_final_location(incoming_path, verdict)
        else:
            verdict = "clean"
            final_path = move_file_to_final_location(incoming_path, verdict)

        print(f"[STORAGE] malwareCount={malware_count}")
        print(f"[STORAGE] malware={malware_info}")
        print(f"[STORAGE] Veredicto final: {verdict}")
        print(f"[STORAGE] Fichero movido a: {final_path}")

    return {
        "filename": upload_file.filename,
        "verdict": verdict,
        "final_path": str(final_path),
        "scan_result": scan_result,
    }