"""
Reports Route — list and retrieve governance reports.

GET  /api/reports/stats
GET  /api/reports
GET  /api/reports/{id}
DELETE /api/reports/{id}
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_supabase
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------------------------------------
# Dashboard Stats
# ---------------------------------------------------------

@router.get("/reports/stats")
async def get_dashboard_stats():
    start = time.perf_counter()
    try:
        supabase = get_supabase()
        all_reports = supabase.table("reports").select(
            "id, state, reporting_month, processed_status, uploaded_at"
        ).execute()

        data = all_reports.data or []
        total = len(data)
        indexed = sum(1 for r in data if r["processed_status"] == "indexed")
        submitted_states = set(r["state"] for r in data)
        states_submitted = len(submitted_states)

        all_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
            "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
            "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Andaman and Nicobar Islands", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
            "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
        ]
        pending_states = sorted(set(all_states) - submitted_states)
        last_updated = max((r["uploaded_at"] for r in data), default=None)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "Dashboard stats served",
            total_reports=total,
            indexed_reports=indexed,
            latency_ms=elapsed_ms,
        )

        return {
            "total_reports": total,
            "indexed_reports": indexed,
            "states_submitted": states_submitted,
            "pending_states": pending_states,
            "last_updated": last_updated,
            "recent_uploads": sorted(
                data,
                key=lambda r: r["uploaded_at"],
                reverse=True,
            )[:10],
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "Dashboard stats failed",
            latency_ms=elapsed_ms,
            error_class=exc.__class__.__name__,
            error=str(exc),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DASHBOARD_STATS_UNAVAILABLE",
                "message": "Dashboard stats are temporarily unavailable. Please retry shortly.",
                "source_error": exc.__class__.__name__,
            },
        )


# ---------------------------------------------------------
# List Reports
# ---------------------------------------------------------

@router.get("/reports")
async def list_reports(
    state: Optional[str] = Query(None),
    reporting_month: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    supabase = get_supabase()

    query = supabase.table("reports").select(
        "id, state, reporting_month, scheme, file_name, "
        "uploaded_at, processed_status, chunk_count"
    ).order("uploaded_at", desc=True).range(
        offset,
        offset + limit - 1,
    )

    if state:
        query = query.eq("state", state)

    if reporting_month:
        query = query.eq("reporting_month", reporting_month)

    if status:
        query = query.eq("processed_status", status)

    result = query.execute()

    return {
        "reports": result.data or [],
        "count": len(result.data or []),
    }


# ---------------------------------------------------------
# Report Detail
# ---------------------------------------------------------

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    supabase = get_supabase()

    report_res = (
        supabase.table("reports")
        .select("*")
        .eq("id", report_id)
        .single()
        .execute()
    )

    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report not found.")

    chunks_res = (
        supabase.table("report_chunks")
        .select(
            "id, chunk_text, section_type, practice_area, "
            "page_number, chunk_index, created_at"
        )
        .eq("report_id", report_id)
        .order("chunk_index")
        .execute()
    )

    return {
        "report": report_res.data,
        "chunks": chunks_res.data or [],
        "chunk_count": len(chunks_res.data or []),
    }


# ---------------------------------------------------------
# Delete Report
# ---------------------------------------------------------

@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    supabase = get_supabase()

    result = (
        supabase.table("reports")
        .delete()
        .eq("id", report_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found.")
    logger.info("Report deleted", report_id=report_id)
    return {
        "success": True,
        "deleted_id": report_id,
    }
