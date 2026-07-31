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


class UploadResponse(BaseModel):
    """Response schema for document upload and ingestion operation."""

    status: str = Field(..., example="success", description="Status of the ingestion operation")
    filename: str = Field(..., example="employee_handbook.pdf", description="Name of the processed file")
    classification: str = Field(..., example="public", description="Security classification ('public' or 'confidential')")
    chunks: int = Field(..., example=18, description="Total number of text chunks ingested")
    collection: str = Field(..., example="enterprise_docs", description="Target vector store collection name")


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and Ingest Document",
    description=(
        "Upload a PDF or DOCX document to be temporarily saved, classified as 'public' or 'confidential', "
        "chunked, embedded, and stored into the ChromaDB vector store."
    ),
)
def upload_document(
    file: UploadFile = File(...),
    classification: str = Form(default="public", description="Document security classification ('public' or 'confidential')"),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> UploadResponse:
    """Handle document upload workflow, validation, temporary persistence, and vector ingestion."""
    logger.info("Received document upload request for file: '%s' (classification='%s')", file.filename, classification)

    if not file.filename or not file.filename.strip():
        logger.warning("Rejected upload request: missing or empty filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    clean_classification = classification.strip().lower()
    if clean_classification not in VALID_CLASSIFICATIONS:
        logger.warning("Rejected upload request: invalid classification '%s'", classification)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Classification must be one of: {', '.join(sorted(VALID_CLASSIFICATIONS))}.",
        )

    filename = file.filename.strip()
    file_path = Path(filename)
    extension = file_path.suffix.lower()

    # 1. Reject unsupported file formats
    if extension not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload for file '%s': unsupported extension '%s'", filename, extension)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension}'. Only PDF (.pdf) and DOCX (.docx) files are supported.",
        )

    # 2. Read file content and reject empty files
    try:
        content = file.file.read()
    except Exception as exc:
        logger.error("Failed to read upload payload for file '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file payload: {exc}",
        )

    if not content or len(content) == 0:
        logger.warning("Rejected upload for file '%s': empty payload", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please provide a valid document with content.",
        )

    # 2b. Enforce 20MB payload size limit
    max_bytes = 20 * 1024 * 1024
    if len(content) > max_bytes:
        logger.warning("Rejected upload for file '%s': size (%d bytes) exceeds 20MB limit", filename, len(content))
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File size exceeds maximum allowed upload limit of 20MB.",
        )

    # 3. Save temporarily inside configured classification subdirectory
    uploads_dir = Path(settings.upload_folder) / clean_classification
    uploads_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = uploads_dir / filename

    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        logger.info("Temporarily stored document payload at '%s'", temp_file_path)

        # 4. Invoke existing IngestionService
        ingestion_result: dict[str, Any] = ingestion_service.ingest(temp_file_path)

        # 5. Return structured JSON matching API response contract
        return UploadResponse(
            status=ingestion_result.get("status", "success"),
            filename=ingestion_result.get("file_name", filename),
            classification=ingestion_result.get("classification", clean_classification),
            chunks=ingestion_result.get("chunks", 0),
            collection=ingestion_result.get("collection", "enterprise_docs"),
        )

    except (ValueError, FileNotFoundError) as exc:
        logger.warning("Validation or file error during ingestion of '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        logger.error("Runtime error during ingestion of '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion service runtime error: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during document upload of '%s': %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during document processing: {exc}",
        )
    finally:
        # 6. Clean up temporary file
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info("Successfully removed temporary file '%s'", temp_file_path)
            except Exception as clean_exc:
                logger.warning("Could not delete temporary file '%s': %s", temp_file_path, clean_exc)
