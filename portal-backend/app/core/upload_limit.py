"""Límite de cuerpo antes del parser multipart, también para cargas sin Content-Length."""
from tempfile import SpooledTemporaryFile
from starlette.responses import JSONResponse
from app.core.config import settings


class UploadLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/files/upload":
            return await self.app(scope, receive, send)
        # Margen para cabeceras y delimitadores multipart; el servicio valida el fichero.
        limit = settings.max_upload_bytes + 1024 * 1024
        size = 0
        with SpooledTemporaryFile(max_size=1024 * 1024) as body:
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                size += len(chunk)
                if size > limit:
                    return await JSONResponse({"detail": "La carga supera el límite de tamaño permitido."}, status_code=413)(scope, receive, send)
                body.write(chunk)
                if not message.get("more_body", False):
                    break
            body.seek(0)
            async def replay():
                chunk = body.read(64 * 1024)
                return {"type": "http.request", "body": chunk, "more_body": body.tell() < size}
            await self.app(scope, replay, send)
