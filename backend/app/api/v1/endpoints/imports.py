"""Portfolio import endpoints — Module 1."""

import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.schemas.import_schema import ImportConfig, ImportPreview, ImportResult
from app.services.import_service import ImportService

router = APIRouter()


@router.post("/preview", response_model=ImportPreview)
async def preview_file(file: UploadFile = File(...)):
    """Upload file and get column preview + suggested mappings."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .xlsx, .xls, or .csv")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    # Save to temp
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    service = ImportService()
    preview = service.generate_preview(file_path, ext)
    return preview


@router.post("/start", response_model=ImportResult)
async def start_import(
    config: ImportConfig,
    file_path: str,
    db: AsyncSession = Depends(get_db),
):
    """Start background import task."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File not found. Upload first via /preview")

    from app.tasks.import_tasks import process_import_task

    task = process_import_task.delay(file_path, config.model_dump())
    return ImportResult(task_id=task.id, status="pending")


@router.get("/status/{task_id}", response_model=ImportResult)
async def get_import_status(task_id: str):
    """Check import task progress."""
    from app.tasks.import_tasks import process_import_task

    result = process_import_task.AsyncResult(task_id)
    if result.state == "PENDING":
        return ImportResult(task_id=task_id, status="pending")
    elif result.state == "PROGRESS":
        info = result.info or {}
        return ImportResult(
            task_id=task_id,
            status="processing",
            total_rows=info.get("total", 0),
            processed=info.get("processed", 0),
            added=info.get("added", 0),
            updated=info.get("updated", 0),
            skipped=info.get("skipped", 0),
        )
    elif result.state == "SUCCESS":
        info = result.result or {}
        return ImportResult(task_id=task_id, status="completed", **info)
    else:
        return ImportResult(task_id=task_id, status="failed", errors=[{"error": str(result.info)}])
