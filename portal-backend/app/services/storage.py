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

# -------------------------------------------------------------------
    # Garantiza que existan las tres zonas documentales:
    # - incoming: staging previo al análisis
    # - clean: archivos admitidos
    # - quarantine: archivos retenidos
    # -------------------------------------------------------------------

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)


def save_file_incoming(upload_file: UploadFile) -> Path:

# -------------------------------------------------------------------
    # Guarda el fichero recibido en la zona incoming.
    # Esta función NO analiza nada: solo persiste el fichero para que
    # después pueda ser escaneado por File Security.
    # -------------------------------------------------------------------

    ensure_directories()

    file_path = INCOMING_DIR / upload_file.filename

    with open(file_path, "wb") as f:
        content = upload_file.file.read()
        f.write(content)

    return file_path


def simulate_file_analysis(filename: str) -> str:

 # -------------------------------------------------------------------
    # Lógica de simulación heredada del proyecto inicial.
    # Actualmente el flujo real usa Trend File Security mediante scan_file().
    # Esta función queda como resto utilitario / referencia de la fase previa.
    # -------------------------------------------------------------------

    suspicious_words = ["virus", "malware", "bad"]

    lower_name = filename.lower()

    for word in suspicious_words:
        if word in lower_name:
            return "quarantine"

    return "clean"


def move_file_to_final_location(source_path: Path, verdict: str) -> Path:

    # -------------------------------------------------------------------
    # Traduce el veredicto lógico en una decisión de almacenamiento:
    # - clean -> carpeta clean
    # - cualquier otro valor distinto de clean -> quarantine
    #
    # Nota: el caso "error" no llega aquí, porque en store_and_classify_file
    # se deja explícitamente el fichero en incoming.
    # -------------------------------------------------------------------

    if verdict == "clean":
        destination = CLEAN_DIR / source_path.name
    else:
        destination = QUARANTINE_DIR / source_path.name

    shutil.move(str(source_path), str(destination))
    return destination


def store_and_classify_file(upload_file: UploadFile) -> dict:

# -------------------------------------------------------------------
    # Orquestador del flujo documental.
    #
    # Secuencia:
    # 1. guardar fichero en incoming
    # 2. llamar a scan_file(...) en file_security.py
    # 3. interpretar el resultado del scanner
    # 4. decidir carpeta final
    # 5. devolver resultado normalizado al endpoint
    # -------------------------------------------------------------------

    print(f"[STORAGE] Procesando fichero: {upload_file.filename}")

    incoming_path = save_file_incoming(upload_file)
    print(f"[STORAGE] Guardado en incoming: {incoming_path}")

    # -------------------------------------------------------------------
    # Integración real con Trend File Security.
    # Esta llamada delega en:
    # - file_security.py -> scan_file(...)
    # que a su vez habla con el scanner gRPC desplegado en Kubernetes.
    # -------------------------------------------------------------------

    scan_result = scan_file(str(incoming_path))
    print(f"[STORAGE] Resultado scan_file(): {scan_result}")

    if scan_result.get("status") == "error":
        verdict = "error"
        final_path = incoming_path
        print("[STORAGE] Veredicto = error, el fichero se queda en incoming")
    else:

# -------------------------------------------------------------------
        # Parseo del resultado técnico devuelto por Trend.
        # La lógica de negocio documental se apoya sobre:
        # - malwareCount
        # - malware
        # - error
        # -------------------------------------------------------------------

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