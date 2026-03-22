from fastapi import APIRouter, UploadFile, File
from app.services.storage import store_and_classify_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = store_and_classify_file(file)

    return {
        "message": "Archivo procesado correctamente",
        "filename": result["filename"],
        "verdict": result["verdict"],
        "final_path": result["final_path"],
    }