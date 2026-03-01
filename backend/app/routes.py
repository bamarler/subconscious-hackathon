import threading

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from .config import settings
from .job_store import create_job, get_job
from .pipeline import run_pipeline_into_job

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "pptx"}


@router.post("/convert")
async def convert_lecture(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a file and start the pipeline. Returns a job_id to stream progress."""
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

    job = create_job()

    t = threading.Thread(
        target=run_pipeline_into_job,
        args=(job, file_bytes, file.filename),
        daemon=True,
    )
    t.start()

    return JSONResponse({"job_id": job.id})


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Quick status check for a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "current_step": job.current_step,
        "event_count": len(job.events),
    }


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str) -> StreamingResponse:
    """SSE stream that replays all completed events, then follows live."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    def generate():
        cursor = 0

        while True:
            # Send any events we haven't sent yet
            while cursor < len(job.events):
                event = job.events[cursor]
                yield f"data: {event.model_dump_json()}\n\n"
                cursor += 1

            # If job is terminal, stop
            if job.status in ("completed", "error"):
                break

            # Wait for new events
            job._notify.wait(timeout=2.0)

    return StreamingResponse(generate(), media_type="text/event-stream")
