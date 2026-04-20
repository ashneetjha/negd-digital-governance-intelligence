"""
Ingest Route — handles file upload + metadata and runs the full ingestion pipeline.

POST /api/ingest
  - file: UploadFile (PDF or DOCX)
  - state: str
  - reporting_month: str (YYYY-MM)
  - scheme: str (optional)
  - semt_team: str (optional JSON string list)
"""

import os
import re
import json
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import get_supabase
from app.services.parsing_service import parse_document
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import store_chunks
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------------------------------------
# Validation Utilities
# ---------------------------------------------------------

def _validate_month_format(month: str):
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REPORTING_MONTH",
                "message": "reporting_month must be in YYYY-MM format.",
            },
        )


# ---------------------------------------------------------
# Background Pipeline (FIXED)
# ---------------------------------------------------------

def _run_pipeline(
    report_id: str,
    file_path: str,
    state: str,
    reporting_month: str,
    scheme: str,
) -> None:
    supabase = get_supabase()

    try:
        # Step 1: mark processing
        supabase.table("reports").update({
            "processed_status": "processing"
        }).eq("id", report_id).execute()

        # Step 2: parse document
        pages = parse_document(file_path)
        logger.info("Parsed text blocks", report_id=report_id, count=len(pages))

        # Step 3: chunking
        chunks = chunk_pages(pages)
        logger.info("Chunks created", report_id=report_id, count=len(chunks))

        # Step 4: store chunks WITH METADATA 
        count = store_chunks(
            report_id=report_id,
            chunks=chunks,
            state=state,
            reporting_month=reporting_month,
            scheme=scheme,
        )
        logger.info("Chunks stored", report_id=report_id, count=count)

        if count == 0:
            raise Exception("CRITICAL: No chunks stored - ingestion invalid")

        # Step 5: mark success
        supabase.table("reports").update({
            "processed_status": "indexed",
            "chunk_count": count,
        }).eq("id", report_id).execute()

        logger.info(
            "Ingestion complete",
            report_id=report_id,
            chunks=count
        )

    except Exception as exc:
        logger.error(
            "Ingestion failed",
            report_id=report_id,
            error=str(exc)
        )

        supabase.table("reports").update({
            "processed_status": "failed",
            "error_message": str(exc)[:500],
        }).eq("id", report_id).execute()

    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


# ---------------------------------------------------------
# API Route (FIXED)
# ---------------------------------------------------------

@router.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    state: str = Form(...),
    reporting_month: str = Form(...),
    scheme: str = Form(default=None),
    semt_team: str = Form(default=None),
):

    # File validation
    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "Only PDF and DOCX files are supported.",
            },
        )

    _validate_month_format(reporting_month)

    # File size check
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.",
            },
        )

    # Save file temporarily
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_ext = ".docx" if "word" in (file.content_type or "") else ".pdf"
    temp_path = os.path.join(settings.UPLOAD_DIR, f"{uuid4()}{file_ext}")

    with open(temp_path, "wb") as f:
        f.write(content)

    # Parse semt_team JSON
    semt_team_data = None
    if semt_team:
        try:
            semt_team_data = json.loads(semt_team)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_SEMT_TEAM_JSON",
                    "message": "semt_team must be valid JSON list.",
                },
            )

    # Insert report metadata
    supabase = get_supabase()
    report_id = str(uuid4())

    supabase.table("reports").insert({
        "id": report_id,
        "state": state,
        "reporting_month": reporting_month,
        "scheme": scheme,
        "file_name": file.filename,
        "semt_team": semt_team_data,
        "processed_status": "pending",
    }).execute()

    # 🔥 CRITICAL FIX: PASS METADATA TO PIPELINE
    background_tasks.add_task(
        _run_pipeline,
        report_id,
        temp_path,
        state,
        reporting_month,
        scheme,
    )

    logger.info(
        "Ingest queued",
        report_id=report_id,
        state=state,
        reporting_month=reporting_month,
    )

    return JSONResponse(
        status_code=202,
        content={
            "report_id": report_id,
            "status": "pending",
            "message": "Report queued for processing. Poll /api/reports/{id} for status.",
        },
    )
