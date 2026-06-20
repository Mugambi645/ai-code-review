"""API routes for the LLM service."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from src.providers.factory import get_provider
from src.analyzer.diff_parser import parse_diff, build_review_context
from src.analyzer.prompts import (
    CODE_REVIEW_SYSTEM,
    SECURITY_AUDIT_SYSTEM,
    REFACTOR_SYSTEM,
    QUICK_SUMMARY_SYSTEM,
)

router = APIRouter()


class ReviewRequest(BaseModel):
    diff: str
    pr_title: str
    pr_body: Optional[str] = ""
    repo: Optional[str] = ""
    pr_number: Optional[int] = None
    review_type: str = "full"  # full | security | refactor | summary


class ReviewResponse(BaseModel):
    review: str
    files_analyzed: int
    provider: str


def get_system_prompt(review_type: str) -> str:
    mapping = {
        "full": CODE_REVIEW_SYSTEM,
        "security": SECURITY_AUDIT_SYSTEM,
        "refactor": REFACTOR_SYSTEM,
        "summary": QUICK_SUMMARY_SYSTEM,
    }
    return mapping.get(review_type, CODE_REVIEW_SYSTEM)


@router.post("/review")
async def review_pr(req: ReviewRequest) -> ReviewResponse:
    """Non-streaming full review."""
    try:
        files = parse_diff(req.diff)
        context = build_review_context(files, req.pr_title, req.pr_body)
        system = get_system_prompt(req.review_type)
        provider = get_provider()
        review_text = await provider.complete(system, context)
        import os
        return ReviewResponse(
            review=review_text,
            files_analyzed=len(files),
            provider=os.getenv("AI_PROVIDER", "anthropic"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/stream")
async def stream_review(req: ReviewRequest):
    """Streaming review — returns Server-Sent Events."""
    files = parse_diff(req.diff)
    context = build_review_context(files, req.pr_title, req.pr_body)
    system = get_system_prompt(req.review_type)
    provider = get_provider()

    async def event_stream():
        import os
        # Send metadata first
        meta = json.dumps({
            "type": "meta",
            "files_analyzed": len(files),
            "provider": os.getenv("AI_PROVIDER", "anthropic"),
        })
        yield f"data: {meta}\n\n"

        try:
            async for token in provider.stream_review(system, context):
                payload = json.dumps({"type": "token", "content": token})
                yield f"data: {payload}\n\n"
        except Exception as e:
            err = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {err}\n\n"
        finally:
            yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/providers")
async def list_providers():
    """List available providers and current selection."""
    import os
    return {
        "current": os.getenv("AI_PROVIDER", "anthropic"),
        "available": ["anthropic", "openai", "huggingface"],
        "models": {
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5"),
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "huggingface": os.getenv("HUGGINGFACE_MODEL", "codellama/CodeLlama-34b-Instruct-hf"),
        },
    }
