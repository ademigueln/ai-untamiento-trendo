import os
from pathlib import Path
from app.services.ai_events import count_ai_events

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

    ai_event_stats = count_ai_events()

    return {
        "incoming_files": incoming_count,
        "clean_files": clean_count,
        "quarantine_files": quarantine_count,
        "blocked_ai_attempts_demo": ai_event_stats["trend_guard_blocked"],
        "total_ai_events": ai_event_stats["total_ai_events"],
        "prompt_injection_blocked": ai_event_stats["prompt_injection_blocked"],
        "sensitive_data_request_blocked": ai_event_stats["sensitive_data_request_blocked"],
        "harmful_output_blocked": ai_event_stats["harmful_output_blocked"],
        "portal_status": "Operativo",
    }