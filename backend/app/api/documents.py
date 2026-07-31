"""Document Management REST API Module for SentinelAI Platform.

Provides REST endpoints for querying document inventory, single-click document deletion with
ChromaDB vector purging and physical file cleanup, and multi-file bulk upload and ingestion.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.llm.config import settings
from app.services.ingestion import IngestionService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Document Management"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
VALID_CLASSIFICATIONS = {"public", "confidential"}


class DocumentItem(BaseModel):
    """Schema for individual document item details."""

    id: str = Field(..., example="doc_a1b2c3d4e5f6", description="Unique document ID")
    name: str = Field(..., example="financial_report_q2_2026.pdf", description="Filename")
    classification: str = Field(..., example="confidential", description="Security classification")
    indexed: bool = Field(True, description="Whether document is indexed in ChromaDB")
    source: str = Field(..., example="Documents/confidential/financial_report_q2_2026.pdf", description="Relative file path")
    chunks: int = Field(..., example=32, description="Vector text chunks count")
    size_bytes: int = Field(0, example=1048576, description="File size in bytes if available")


class DeleteDocumentResponse(BaseModel):
    """Response schema for document deletion operation."""

    status: str = Field("success", example="success")
    message: str = Field(..., example="Document deleted successfully.")
    deleted_document_id: str = Field(..., example="doc_a1b2c3d4e5f6")
    filename: str = Field(..., example="financial_report_q2_2026.pdf")
    classification: str = Field(..., example="confidential")
    deleted_chunks: int = Field(..., example=32)


class BulkUploadResponse(BaseModel):
    """Response schema for multi-file bulk upload and auto-ingestion."""

    status: str = Field("completed", example="completed")
    processed: int = Field(..., example=3)
    successful: int = Field(..., example=3)
    failed: int = Field(0, example=0)
    results: list[dict[str, Any]] = Field(default_factory=list)


def _get_document_map_from_chromadb(request: Request) -> dict[str, dict[str, Any]]:
    """Helper querying ChromaDB collections to build comprehensive document inventory."""
    vector_store = getattr(request.app.state, "vector_store", None)
    protected_vault = getattr(request.app.state, "protected_vault", None)

    if vector_store is None:
        try:
            vector_store = VectorStore(collection_name="enterprise_docs")
        except Exception:
            pass

    if protected_vault is None:
        try:
            protected_vault = VectorStore(collection_name="protected_vault")
        except Exception:
            pass

    doc_map: dict[str, dict[str, Any]] = {}

    def _process_collection(col_store: Any, default_classif: str) -> None:
        if not col_store or not hasattr(col_store, "_collection"):
            return
        try:
            res = col_store._collection.get(include=["metadatas"])
            metadatas = res.get("metadatas") or []
            for meta in metadatas:
                if not meta:
                    continue
                source = meta.get("source") or "unknown_document"
                classif = meta.get("classification") or default_classif
                doc_id = meta.get("document_id") or f"doc_{hashlib.md5(source.encode('utf-8')).hexdigest()[:12]}"
                file_path_str = meta.get("file_path") or f"Documents/{classif}/{source}"

                if doc_id not in doc_map:
                    # Calculate disk file size if file exists
                    size_b = 0
                    p = Path(file_path_str)
                    if p.exists() and p.is_file():
                        size_b = p.stat().st_size
                    else:
                        # Check alternate search locations
                        for search_p in [
                            Path("Documents") / classif / source,
                            Path(settings.upload_folder) / classif / source,
                        ]:
                            if search_p.exists() and search_p.is_file():
                                size_b = search_p.stat().st_size
                                file_path_str = str(search_p)
                                break

                    rel_source = file_path_str if file_path_str.startswith("Documents/") or file_path_str.startswith("uploads/") else f"Documents/{classif}/{source}"

                    doc_map[doc_id] = {
                        "id": doc_id,
                        "name": source,
                        "classification": classif,
                        "indexed": True,
                        "source": rel_source,
                        "file_path": file_path_str,
                        "chunks": 0,
                        "size_bytes": size_b,
                    }
                doc_map[doc_id]["chunks"] += 1
                if default_classif == "confidential":
                    doc_map[doc_id]["classification"] = "confidential"
        except Exception as exc:
            logger.error("Failed to query collection metadata: %s", exc)

    _process_collection(vector_store, "public")
    _process_collection(protected_vault, "confidential")

    return doc_map


@router.get(
    "",
    response_model=list[DocumentItem],
    status_code=status.HTTP_200_OK,
    summary="List Document Inventory",
    description="Retrieve all indexed documents in knowledge base with document IDs, chunk counts, and metadata.",
)
def list_documents(request: Request) -> list[DocumentItem]:
    """Return comprehensive list of stored documents from ChromaDB."""
    logger.info("Received request for document inventory list")
    doc_map = _get_document_map_from_chromadb(request)

    return [
        DocumentItem(
            id=d["id"],
            name=d["name"],
            classification=d["classification"],
            indexed=d["indexed"],
            source=d["source"],
            chunks=d["chunks"],
            size_bytes=d["size_bytes"],
        )
        for d in doc_map.values()
    ]


@router.delete(
    "/{document_id}",
    response_model=DeleteDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description=(
        "Permanently delete a document by Document ID. Purges vector chunk embeddings from ChromaDB "
        "collections, removes physical files from disk, records audit events, and updates telemetry."
    ),
)
def delete_document(document_id: str, request: Request) -> DeleteDocumentResponse:
    """Safely delete document vectors and physical files by document_id."""
    logger.info("Received request to delete document_id: '%s'", document_id)

    if not document_id or not document_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="document_id cannot be empty.")

    clean_id = document_id.strip()
    doc_map = _get_document_map_from_chromadb(request)

    target_doc = doc_map.get(clean_id)
    if not target_doc:
        # Check if caller passed exact filename instead of document_id
        for d_id, d_data in doc_map.items():
            if d_data["name"].strip().lower() == clean_id.lower():
                target_doc = d_data
                clean_id = d_id
                break

    if not target_doc:
        logger.warning("Delete failed: document_id '%s' not found in inventory", document_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' was not found in index.",
        )

    filename = target_doc["name"]
    classification = target_doc["classification"]
    saved_path_str = target_doc.get("file_path", "")

    # 1. Purge vectors from primary collection (enterprise_docs)
    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        vector_store = VectorStore(collection_name="enterprise_docs")

    deleted_chunks = vector_store.delete_documents_by_document_id(clean_id, source=filename)

    # 2. Purge vectors from protected_vault if confidential
    if classification == "confidential":
        protected_vault = getattr(request.app.state, "protected_vault", None)
        if protected_vault is None:
            protected_vault = VectorStore(collection_name="protected_vault")
        vault_deleted = protected_vault.delete_documents_by_document_id(clean_id, source=filename)
        deleted_chunks = max(deleted_chunks, vault_deleted)

    # 3. Physical file deletion on disk
    file_removed = False
    candidate_paths = [
        Path(saved_path_str),
        Path("Documents") / classification / filename,
        Path(settings.upload_folder) / classification / filename,
        Path("Documents") / "public" / filename,
        Path("Documents") / "confidential" / filename,
    ]

    for p in candidate_paths:
        if p and p.exists() and p.is_file():
            try:
                p.unlink()
                file_removed = True
                logger.info("Successfully deleted physical file at '%s'", str(p))
            except Exception as exc:
                logger.error("Failed to delete physical file '%s': %s", str(p), exc)

    # 4. Log Security/System Audit Event
    try:
        audit_logger = getattr(request.app.state, "audit_logger", None)
        if audit_logger:
            audit_logger.log_event(
                question=f"DELETE /api/documents/{clean_id}",
                decision="SYSTEM_ACTION",
                severity="LOW",
                categories=["DOCUMENT_MANAGEMENT"],
                reason=f"Permanently deleted document '{filename}' ({classification}) and purged {deleted_chunks} vector chunk(s).",
                matched_document=filename,
                confidence=1.0,
                policy_violation=False,
            )
    except Exception as audit_exc:
        logger.error("Failed to record deletion audit event: %s", audit_exc)

    return DeleteDocumentResponse(
        status="success",
        message=f"Document '{filename}' deleted successfully.",
        deleted_document_id=clean_id,
        filename=filename,
        classification=classification,
        deleted_chunks=deleted_chunks,
    )



