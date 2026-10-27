from fastapi import APIRouter, UploadFile, File
from app.services.storage import store_and_classify_file

router = APIRouter()


@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    # FastAPI ejecuta las rutas síncronas en su pool de hilos.
    try:
        return store_and_classify_file(file)
    finally:
        file.file.close()
