from pathlib import Path
from app.core.config import settings
from app.services.ai_events import count_ai_events, get_service_health


def count_files_in_folder(folder: Path) -> int:
    return sum(1 for item in folder.iterdir() if item.is_file()) if folder.exists() else 0


def get_portal_stats() -> dict:
    health = get_service_health()
    if any(state in ("unavailable", "not_configured") for state in health.values()):
        status = "Degradado"
    elif all(state == "available" for state in health.values()):
        status = "Operativo"
    else:
        status = "Pendiente de verificar"
    events = count_ai_events()
    return {**{f"{folder}_files": count_files_in_folder(settings.upload_dir / folder) for folder in ("incoming", "clean", "quarantine")},
            **events, "blocked_ai_attempts_demo": events["trend_guard_blocked"],
            "portal_status": status, "services": health,
            "guard_policy": "permissive" if settings.guard_fail_open else "strict",
            "event_retention_days": settings.event_retention_days}
