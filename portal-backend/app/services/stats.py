import os
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))


def count_files_in_folder(folder: Path) -> int:
    if not folder.exists():
        return 0

    return sum(1 for item in folder.iterdir() if item.is_file())


def get_portal_stats() -> dict:
    incoming_dir = UPLOAD_DIR / "incoming"
    clean_dir = UPLOAD_DIR / "clean"
    quarantine_dir = UPLOAD_DIR / "quarantine"

    incoming_count = count_files_in_folder(incoming_dir)
    clean_count = count_files_in_folder(clean_dir)
    quarantine_count = count_files_in_folder(quarantine_dir)

    # Este valor NO es real todavía.
    # Es un placeholder para demo hasta que exista integración real con guardrails.
    blocked_ai_attempts_demo = 3

    return {
        "incoming_files": incoming_count,
        "clean_files": clean_count,
        "quarantine_files": quarantine_count,
        "blocked_ai_attempts_demo": blocked_ai_attempts_demo,
        "portal_status": "Operativo",
    }
