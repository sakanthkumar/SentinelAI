"""Chat and RAG query API endpoint module for SentinelAI platform."""

from functools import lru_cache
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.ai.rag_pipeline import RAGPipeline
from app.ai.retriever import Retriever
from app.detection.leak_detector import LeakDetector
from app.llm.base import BaseLLM
from app.llm.factory import LLMFactory
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat & RAG"])


@lru_cache
def _get_default_rag_pipeline() -> RAGPipeline:
    """Fallback singleton getter for RAGPipeline if not available on application state."""
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    retriever = Retriever(embedding_service=embedding_service, vector_store=vector_store)
    llm: BaseLLM = LLMFactory.get_provider()
    leak_detector = LeakDetector()
    return RAGPipeline(
        retriever=retriever,
        llm=llm,
        leak_detector=leak_detector,
    )


def get_rag_pipeline(request: Request) -> RAGPipeline:
    """Dependency provider retrieving RAGPipeline from FastAPI application state."""
    pipeline = getattr(request.app.state, "rag_pipeline", None)
    if pipeline is None:
        pipeline = _get_default_rag_pipeline()
    return pipeline


class ChatRequest(BaseModel):
    """Request schema for RAG chat endpoint."""

    question: str = Field(
        ...,
        example="What is the leave policy?",
        description="User query string to be answered using document context",
    )
    top_k: int = Field(
        default=5,
        example=5,
        description="Number of top document context chunks to retrieve",
    )


class ChatResponse(BaseModel):
    """Response schema for RAG chat endpoint."""

    question: str = Field(..., example="What is the leave policy?")
    answer: str = Field(..., example="The leave policy allows 20 days paid leave.")
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of retrieved source document chunks and metadata",
    )
    retrieved_documents: int = Field(
        ...,
        example=5,
        description="Count of retrieved context documents used for generation",
    )
    leak_detection: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed leak detection security evaluation report",
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Chat Query",
    description=(
        "Submit a user question to the SentinelAI RAG Pipeline. "
        "Retrieves relevant document chunks, synthesizes a grounded answer via LLM, "
        "and evaluates the answer for exfiltration risks via LeakDetector."
    ),
)
async def chat_query(
    request: ChatRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> ChatResponse:
    """Orchestrate chat query execution using existing RAGPipeline."""
    logger.info("Received chat query request")

    # 1. Reject empty questions
    if not request.question or not request.question.strip():
        logger.warning("Rejected chat query: question is empty or whitespace")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace.",
        )

    # 2. Validate top_k > 0
    if request.top_k <= 0:
        logger.warning("Rejected chat query: top_k (%d) must be > 0", request.top_k)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k must be a positive integer greater than 0.",
        )

    clean_question = request.question.strip()

    # 3. Call existing RAGPipeline.ask()
    try:
        pipeline_output: dict[str, Any] = rag_pipeline.ask(
            question=clean_question,
            top_k=request.top_k,
        )

        # 4. Return pipeline response formatted according to response contract
        return ChatResponse(
            question=pipeline_output.get("question", clean_question),
            answer=pipeline_output.get("answer", ""),
            sources=pipeline_output.get("sources", []),
            retrieved_documents=pipeline_output.get("retrieved_documents", 0),
            leak_detection=pipeline_output.get("leak_detection", {}),
        )

    except ValueError as exc:
        logger.warning("Validation or retrieval error in RAGPipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        logger.error("Runtime error in RAGPipeline execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline execution failure: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error in chat endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while executing chat query: {exc}",
        )
