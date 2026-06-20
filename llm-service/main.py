"""
AI Code Review - LLM Orchestration Service
FastAPI app with pluggable AI provider support.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from src.api.routes import router
from src.providers.factory import get_provider

load_dotenv()

app = FastAPI(
    title="AI Code Review - LLM Service",
    description="Pluggable LLM orchestration for code review, security audits, and refactor suggestions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    provider = os.getenv("AI_PROVIDER", "anthropic")
    return {"status": "ok", "provider": provider}


@app.get("/")
async def root():
    return {"service": "llm-service", "version": "1.0.0"}
