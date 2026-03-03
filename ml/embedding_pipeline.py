"""
Standalone Embedding Pipeline — batch-processes all indexed reports
or a single report by ID.

Usage:
  python embedding_pipeline.py                     # re-embed all reports
  python embedding_pipeline.py --report-id <uuid>  # re-embed one report
"""
import argparse
import sys
import os

# Add backend to path so we can import from app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.db.database import get_supabase
from app.services.parsing_service import parse_document
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import store_chunks, embed_texts
from app.utils.logger import get_logger

logger = get_logger("embedding_pipeline")


def re_embed_report(report_id: str):
    """Delete existing chunks for a report and re-embed its source document."""
    supabase = get_supabase()

    # Fetch report
    report = supabase.table("reports").select("*").eq("id", report_id).single().execute().data
    if not report:
        logger.error("Report not found", report_id=report_id)
        return

    logger.info("Re-embedding report", report_id=report_id, state=report["state"], month=report["month"])

    # Delete existing chunks
    supabase.table("report_chunks").delete().eq("report_id", report_id).execute()

    # Note: file is not stored persistently in this demo setup.
    # For production, store file_url in object storage (e.g. Supabase Storage)
    # and download before parsing.
    logger.warning("File re-download from storage not implemented in this pipeline. Use backend ingest endpoint.")


def list_all_reports():
    """Return all report IDs with their state, month and status."""
    supabase = get_supabase()
    data = supabase.table("reports").select("id, state, month, processed_status, chunk_count").execute().data
    return data or []


def main():
    parser = argparse.ArgumentParser(description="NeGD Embedding Pipeline")
    parser.add_argument("--report-id", help="UUID of a specific report to re-embed")
    parser.add_argument("--list", action="store_true", help="List all reports")
    args = parser.parse_args()

    if args.list:
        reports = list_all_reports()
        print(f"\n{'ID':<38} {'State':<22} {'Month':<10} {'Status':<12} {'Chunks'}")
        print("-" * 90)
        for r in reports:
            print(f"{r['id']:<38} {r['state']:<22} {r['month']:<10} {r['processed_status']:<12} {r['chunk_count']}")
        print(f"\nTotal: {len(reports)} reports")
        return

    if args.report_id:
        re_embed_report(args.report_id)
    else:
        reports = list_all_reports()
        logger.info("Processing all reports", count=len(reports))
        for report in reports:
            if report["processed_status"] == "indexed":
                logger.info("Skipping already-indexed report", report_id=report["id"])
            else:
                re_embed_report(report["id"])


if __name__ == "__main__":
    main()
