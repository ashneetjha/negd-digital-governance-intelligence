"""
Analysis Route — RAG-based query with citation grounding.

POST /api/analysis
  - prompt: str
  - state: Optional[str]
  - month: Optional[str]
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag_service import run_rag
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AnalysisRequest(BaseModel):
    prompt: str
    state: Optional[str] = None
    month: Optional[str] = None


@router.post("/analysis")
async def run_analysis(request: AnalysisRequest):
    """
    Run a RAG-based analysis query over indexed governance reports.
    Returns a citation-grounded answer with source metadata.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    if len(request.prompt) > 2000:
        raise HTTPException(status_code=400, detail="Prompt exceeds 2000 character limit.")

    try:
        result = run_rag(
            prompt=request.prompt,
            state=request.state,
            month=request.month,
        )
        logger.info(
            "Analysis served",
            chunks=result.chunks_retrieved,
            state=request.state,
            month=request.month,
        )
        return {
            "success": True,
            "data": result.to_dict(),
        }
    except RuntimeError as exc:
        message = str(exc)
        if "GROQ_API_KEY" in message:
            raise HTTPException(
                status_code=503,
                detail={"code": "AI_NOT_CONFIGURED", "message": "AI service not configured."},
            )
        if "STRICT_REAL_AI" in message or "Embedding model unavailable" in message:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "EMBEDDING_DEPENDENCY_UNAVAILABLE",
                    "message": "Embedding dependency unavailable in strict AI mode.",
                },
            )
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_DEPENDENCY_UNAVAILABLE", "message": message},
        )
    except Exception as exc:
        logger.error("Analysis error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal analysis error.")
