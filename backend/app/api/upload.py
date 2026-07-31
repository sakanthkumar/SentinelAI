"""Document upload and ingestion API endpoint module for SentinelAI platform."""

from functools import lru_cache
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.llm.config import settings
from app.services.chunking import TextChunker
from app.services.document_loader import DocumentLoader
from app.services.embeddings import EmbeddingService
from app.services.ingestion import IngestionService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Ingestion"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
VALID_CLASSIFICATIONS = {"public", "confidential"}


@lru_cache
def _get_default_ingestion_service() -> IngestionService:
    """Fallback singleton getter for IngestionService if not available on application state."""
    loader = DocumentLoader()
    chunker = TextChunker()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    return IngestionService(
        loader=loader,
        chunker=chunker,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def get_ingestion_service(request: Request) -> IngestionService:
    """Dependency provider retrieving IngestionService from FastAPI application state."""
    service = getattr(request.app.state, "ingestion_service", None)
    if service is None:
        service = _get_default_ingestion_service()
    return service


class FileIngestionItemResult(BaseModel):
    """Schema detailing result for individual document file ingestion."""

    filename: str = Field(..., example="employee_handbook.pdf", description="Name of the processed file")
    status: str = Field(..., example="success", description="Status ('success' or 'failed')")
    classification: str = Field("public", example="public", description="Security classification")
    chunks: int = Field(0, example=18, description="Number of text chunks ingested")
    collection: str = Field("enterprise_docs", example="enterprise_docs", description="Target vector store collection")
    error: str | None = Field(None, example="File size exceeds 20MB limit.", description="Error message if failed")


class UploadResponse(BaseModel):
    """Response schema for unified multi-file upload and ingestion operation."""

    status: str = Field("completed", example="completed", description="Overall ingestion status")
    processed: int = Field(..., example=1, description="Total files processed")
    successful: int = Field(..., example=1, description="Count of successfully ingested files")
    failed: int = Field(0, example=0, description="Count of failed files")
    results: list[FileIngestionItemResult] = Field(default_factory=list, description="Per-file detailed results")

    # Compatibility fields for legacy single-file clients
    filename: str = Field("", example="employee_handbook.pdf", description="Primary filename")
    classification: str = Field("public", example="public", description="Primary security classification")
    chunks: int = Field(0, example=18, description="Primary chunks count")
    collection: str = Field("enterprise_docs", example="enterprise_docs", description="Primary collection")


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and Ingest Documents",
    description=(
        "Upload one or multiple PDF/DOCX documents, classify them as 'public' or 'confidential', "
        "chunk, embed, and store them into ChromaDB vector stores."
    ),
)
def upload_documents(
    request: Request,
    files: list[UploadFile] = File(None),
    file: UploadFile = File(None),
    classification: str = Form(default="public", description="Security classification ('public' or 'confidential')"),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> UploadResponse:
    """Handle multi-file document upload, validation, batch ingestion, and audit logging."""
    clean_classification = classification.strip().lower()
    if clean_classification not in VALID_CLASSIFICATIONS:
        logger.warning("Rejected upload request: invalid classification '%s'", classification)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Classification must be one of: {', '.join(sorted(VALID_CLASSIFICATIONS))}.",
        )

    target_files: list[UploadFile] = []
    if files:
        target_files.extend(files)
    if file and file not in target_files:
        target_files.append(file)

    if not target_files:
        logger.warning("Rejected upload request: no files provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided for upload.",
        )

    logger.info("Processing upload request for %d file(s) (classification='%s')", len(target_files), clean_classification)

    max_bytes = 20 * 1024 * 1024  # 20MB payload limit
    results: list[FileIngestionItemResult] = []
    successful = 0
    failed = 0

    for file_obj in target_files:
        raw_name = file_obj.filename or "unnamed_document"
        clean_name = raw_name.strip()
        ext = Path(clean_name).suffix.lower()

        # 1. Reject invalid extensions
        if ext not in ALLOWED_EXTENSIONS:
            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="failed",
                    classification=clean_classification,
                    chunks=0,
                    error=f"Unsupported file type '{ext}'. Only .pdf and .docx allowed.",
                )
            )
            failed += 1
            continue

        # 2. Read content and validate non-empty and max size
        try:
            content = file_obj.file.read()
        except Exception as read_exc:
            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="failed",
                    classification=clean_classification,
                    chunks=0,
                    error=f"Failed to read payload: {read_exc}",
                )
            )
            failed += 1
            continue

        if not content or len(content) == 0:
            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="failed",
                    classification=clean_classification,
                    chunks=0,
                    error="File is empty.",
                )
            )
            failed += 1
            continue

        if len(content) > max_bytes:
            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="failed",
                    classification=clean_classification,
                    chunks=0,
                    error="File size exceeds maximum 20MB limit.",
                )
            )
            failed += 1
            continue

        # 3. Save temporary file in Documents/{classification}/
        target_dir = Path("Documents") / clean_classification
        target_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = target_dir / clean_name

        try:
            with open(temp_file_path, "wb") as f:
                f.write(content)

            # 4. Ingest file into ChromaDB
            ingest_res = ingestion_service.ingest(temp_file_path, classification=clean_classification)

            # 5. Log Security Audit Event
            try:
                audit_logger = getattr(request.app.state, "audit_logger", None)
                if audit_logger:
                    audit_logger.log_event(
                        question=f"UPLOAD /upload '{clean_name}'",
                        decision="SYSTEM_ACTION",
                        severity="LOW",
                        categories=["DOCUMENT_MANAGEMENT"],
                        reason=f"Uploaded and ingested '{clean_name}' ({clean_classification}) into vector store ({ingest_res.get('chunks', 0)} chunks).",
                        matched_document=clean_name,
                        confidence=1.0,
                    )
            except Exception:
                pass

            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="success",
                    classification=clean_classification,
                    chunks=ingest_res.get("chunks", 0),
                    collection=ingest_res.get("collection", "enterprise_docs"),
                )
            )
            successful += 1

        except Exception as exc:
            logger.error("Failed to ingest file '%s': %s", clean_name, exc)
            results.append(
                FileIngestionItemResult(
                    filename=clean_name,
                    status="failed",
                    classification=clean_classification,
                    chunks=0,
                    error=str(exc),
                )
            )
            failed += 1

    first_success = next((r for r in results if r.status == "success"), None) or (results[0] if results else None)

    return UploadResponse(
        status="completed",
        processed=len(target_files),
        successful=successful,
        failed=failed,
        results=results,
        filename=first_success.filename if first_success else "",
        classification=first_success.classification if first_success else clean_classification,
        chunks=first_success.chunks if first_success else 0,
        collection=first_success.collection if first_success else "enterprise_docs",
    )
