"""
Chat Route — General-purpose NeGD Governance Chatbot

POST /api/chat
  - message: str          (required)
  - history: list[dict]   (optional, [{role, content}])
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_service import run_chat
from app.utils.logger import get_logger
from app.utils.response_formatter import build_intelligence_response

router = APIRouter()
logger = get_logger(__name__)


class ChatTurn(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatTurn]] = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    General-purpose Digital India governance chatbot.
    Does NOT perform document retrieval — answers from LLM knowledge + governance context.
    For document-grounded answers, use /api/analysis instead.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if len(request.message) > 2000:
        raise HTTPException(status_code=400, detail="Message exceeds 2000 character limit.")

    # Convert history to plain dicts
    history_dicts = (
        [{"role": t.role, "content": t.content} for t in request.history]
        if request.history
        else None
    )

    try:
        result = run_chat(message=request.message, history=history_dicts)
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        metadata = dict(result.get("metadata", {}))
        metadata.setdefault("route", "chat")
        metadata.setdefault("confidence", 0.7)
        metadata.setdefault("latency", metadata.get("latency_ms", 0.0))

        return build_intelligence_response(
            answer=answer,
            structured={
                "summary": answer,
                "key_insights": [],
                "changes_detected": [],
                "risks": [],
                "status": "stable",
                "confidence": float(metadata.get("confidence", 0.7)),
                "sources": sources,
            },
            sources=sources,
            metadata=metadata,
            data=result,
        )

    except Exception as exc:
        logger.error("Chat endpoint error", error=str(exc))
        fallback = run_chat(message=request.message, history=history_dicts)
        answer = fallback.get("answer", "Chat service temporarily unavailable")
        sources = fallback.get("sources", [])
        metadata = dict(fallback.get("metadata", {}))
        metadata.setdefault("route", "chat")
        metadata.setdefault("confidence", 0.0)
        metadata.setdefault("latency", metadata.get("latency_ms", 0.0))
        return build_intelligence_response(
            answer=answer,
            structured={
                "summary": answer,
                "key_insights": [],
                "changes_detected": [],
                "risks": [fallback.get("details", str(exc))],
                "status": "limited",
                "confidence": float(metadata.get("confidence", 0.0)),
                "sources": sources,
            },
            sources=sources,
            metadata=metadata,
            data=fallback,
        )
