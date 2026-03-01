from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config import settings
from .pipeline import run_pipeline

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "pptx"}


@router.post("/convert")
async def convert_lecture(file: UploadFile = File(...)) -> StreamingResponse:
    if not settings.subconscious_api_key:
        raise HTTPException(status_code=500, detail="SUBCONSCIOUS_API_KEY not configured")
    if not settings.fal_key:
        raise HTTPException(status_code=500, detail="FAL_KEY not configured")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Use .pdf or .pptx",
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    file_bytes = await file.read()
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.max_upload_mb} MB",
        )

    filename = file.filename

    def generate():
        for event in run_pipeline(file_bytes, filename):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
