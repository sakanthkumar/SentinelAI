"""Knowledge Base bulk ingestion API endpoint module for SentinelAI platform."""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Knowledge Base Ingestion"])


def get_documents_directory() -> Path:
    """Locate root Documents directory across project workspace layouts."""
    # 1. Base directory (e.g. d:\SentinelAI\Documents)
    base_dir = Path(__file__).resolve().parents[3]
    docs_dir = base_dir / "Documents"
    if docs_dir.exists() and docs_dir.is_dir():
        return docs_dir

    # 2. Backend relative (e.g. d:\SentinelAI\backend\Documents)
    backend_docs_dir = Path(__file__).resolve().parents[1] / "Documents"
    if backend_docs_dir.exists() and backend_docs_dir.is_dir():
        return backend_docs_dir

    # Default fallback
    return docs_dir


def get_ingestion_service(request: Request) -> IngestionService:
    """Dependency provider retrieving IngestionService from FastAPI application state."""
    service = getattr(request.app.state, "ingestion_service", None)
    if service is None:
        from app.api.upload import _get_default_ingestion_service
        service = _get_default_ingestion_service()
    return service


class FailureDetail(BaseModel):
    """Schema detailing individual document ingestion failures."""

    file: str = Field(..., example="financial_report.pdf", description="Name of the failed file")
    reason: str = Field(..., example="Corrupted PDF", description="Error justification")


class BulkIngestResponse(BaseModel):
    """Response schema for bulk knowledge base ingestion operation."""

    status: str = Field(..., example="success", description="Overall ingestion status")
    documents_processed: int = Field(..., example=9, description="Total successfully processed documents")
    public_documents: int = Field(..., example=4, description="Count of public documents processed")
    confidential_documents: int = Field(..., example=5, description="Count of confidential documents processed")
    total_chunks: int = Field(..., example=218, description="Total number of text chunks stored")
    failed_documents: int = Field(..., example=0, description="Count of failed documents")
    failures: list[FailureDetail] = Field(default_factory=list, description="List of failed document details")
    processing_time_seconds: float = Field(..., example=11.84, description="Elapsed wall-clock processing time in seconds")


@router.post(
    "/api/knowledge-base/ingest",
    response_model=BulkIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk Ingest Knowledge Base",
    description=(
        "Recursively scan the root Documents directory (public/ and confidential/ subdirectories) "
        "and bulk ingest all supported documents (.pdf, .docx) into the ChromaDB vector store."
    ),
)
async def bulk_ingest_knowledge_base(
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> BulkIngestResponse:
    """Orchestrate bulk knowledge base document ingestion."""
    logger.info("Received request for bulk knowledge base ingestion")

    docs_dir = get_documents_directory()
    logger.info("Targeting root Documents directory at '%s'", docs_dir)

    if not docs_dir.exists():
        logger.error("Root Documents directory not found at '%s'", docs_dir)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root Documents directory not found at '{docs_dir}'. Please ensure the Documents folder exists.",
        )

    try:
        summary: dict[str, Any] = ingestion_service.ingest_directory(docs_dir)
        return BulkIngestResponse(**summary)

    except FileNotFoundError as exc:
        logger.error("Directory not found during bulk ingestion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        logger.warning("Validation error during bulk ingestion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected error during bulk ingestion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk ingestion failure: {exc}",
        )
