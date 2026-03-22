import os
import shutil
from pathlib import Path
from fastapi import UploadFile

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
    incoming_path = save_file_incoming(upload_file)

    verdict = simulate_file_analysis(upload_file.filename)

    final_path = move_file_to_final_location(incoming_path, verdict)

    return {
        "filename": upload_file.filename,
        "verdict": verdict,
        "final_path": str(final_path),
    }