import logging
from time import perf_counter
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.upload_limit import UploadLimitMiddleware
from app.routes.chat import router as chat_router
from app.routes.files import router as files_router
from app.routes.stats import router as stats_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("portal")
app = FastAPI()
app.add_middleware(UploadLimitMiddleware)
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])
app.include_router(chat_router, prefix="/api/chat")
app.include_router(files_router, prefix="/api/files")
app.include_router(stats_router, prefix="/api/stats")


@app.middleware("http")
async def request_log(request: Request, call_next):
    request_id = uuid4().hex
    started = perf_counter()
    response = await call_next(request)
    # No registrar URL ni path: DELETE contiene el token de conversación.
    logger.info("request_completed id=%s method=%s status=%s duration_ms=%.1f", request_id, request.method, response.status_code, (perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    # Preparación local; no consume llamadas de pago a proveedores.
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    from app.services.ai_events import count_ai_events
    count_ai_events()
    return {"status": "ready"}
