"""Document Ingestion Service Module for SentinelAI Platform."""
import logging
from pathlib import Path
import re
import time
from typing import Any

from app.services.chunking import TextChunker
from app.services.document_loader import DocumentLoader
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

VALID_CLASSIFICATIONS = {"public", "confidential"}
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class IngestionService:
    """Orchestrates document loading, text chunking, embedding generation, deduplication, and vector persistence."""

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        chunker: TextChunker | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
        protected_vault: VectorStore | None = None,
    ) -> None:
        """Initialize IngestionService with optional injected dependencies.

        Args:
            loader (DocumentLoader | None): Document loading component.
            chunker (TextChunker | None): Text splitting component.
            embedding_service (EmbeddingService | None): Vector embedding component.
            vector_store (VectorStore | None): Persistent vector database component.
            protected_vault (VectorStore | None): Persistent vector database component for protected vault.
        """
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or TextChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.protected_vault = protected_vault or VectorStore(collection_name="protected_vault")

    def _determine_classification(self, path: Path) -> str:
        """Automatically determine security classification ('public' or 'confidential') from document file path.

        Args:
            path (Path): Path instance of the target document.

        Returns:
            str: Classification label ('public' or 'confidential').

        Raises:
            ValueError: If the document is not inside either a 'public' or 'confidential' directory.
        """
        resolved_parts = [part.lower() for part in path.resolve().parts]
        raw_parts = [part.lower() for part in path.parts]
        all_parts = set(resolved_parts + raw_parts)

        if "public" in all_parts:
            return "public"
        elif "confidential" in all_parts:
            return "confidential"
        else:
            raise ValueError(
                f"Document '{path.name}' must reside inside a 'public' or 'confidential' directory. "
                f"File path '{path}' does not contain a valid classification directory in its hierarchy."
            )

    def _determine_document_type(self, path: Path) -> str:
        """Infer document type category from filename stem (e.g., 'financial', 'leave', 'database', 'api').

        Args:
            path (Path): Target document file path.

        Returns:
            str: Extracted document type label.
        """
        stem_lower = path.stem.lower()
        parts = re.split(r"[_\-\s]+", stem_lower)
        return parts[0] if parts and parts[0] else "general"

    def ingest(self, file_path: str | Path, classification: str | None = None) -> dict[str, Any]:
        """Ingest a file into the vector database with automated classification, document typing, and deduplication.

        Workflow:
        Path classification check -> Document type inference -> DocumentLoader -> TextChunker
        -> Deduplication check & deletion -> EmbeddingService -> VectorStore metadata enrichment

        Args:
            file_path (str | Path): Path to document file (PDF, DOCX).
            classification (str | None): Optional explicit security classification ('public' or 'confidential').

        Returns:
            dict[str, Any]: Ingestion statistics including status, chunk count, collection name, classification, and document_type.

        Raises:
            FileNotFoundError: If the input file does not exist.
            ValueError: If file is invalid, empty, or not in a 'public' or 'confidential' directory.
            RuntimeError: If document processing or storage fails.
        """
        path = Path(file_path)
        logger.info("Starting ingestion for file: '%s'", path.name)

        if not path.exists():
            raise FileNotFoundError(f"Target ingestion document not found at path: '{path}'")

        # 1. Infer classification if not provided explicitly
        if not classification:
            classification = self._determine_classification(path)
        else:
            classification = classification.strip().lower()

        document_type = self._determine_document_type(path)
        logger.info(
            "Classified document '%s' as classification='%s', document_type='%s'.",
            path.name,
            classification,
            document_type,
        )

        # 2. Load document text
        raw_text = self.loader.load(path)

        # 3. Split text into chunks
        chunks = self.chunker.split_text(raw_text)

        # 4. Detect and delete existing vectors for this document to prevent duplicate indexing
        deleted_count = self.vector_store.delete_documents_by_source(path.name)
        if deleted_count > 0:
            logger.info(
                "Existing vectors removed for source file '%s': %d chunk(s) deleted.",
                path.name,
                deleted_count,
            )

        # 5. Generate embeddings for chunks
        embeddings = self.embedding_service.embed_documents(chunks)

        # 6. Generate deterministic IDs and metadata for each chunk containing classification and document_type
        import hashlib
        doc_id = f"doc_{hashlib.md5(path.name.encode('utf-8')).hexdigest()[:12]}"
        doc_id_prefix = path.stem
        chunk_ids = [f"{doc_id_prefix}_{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc_id,
                "source": path.name,
                "classification": classification,
                "document_type": document_type,
                "chunk_index": idx,
                "file_path": str(path.resolve()),
            }
            for idx in range(len(chunks))
        ]

        # 7. Store new chunks in vector database
        self.vector_store.add_documents(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        if classification == "confidential":
            vault_deleted = self.protected_vault.delete_documents_by_source(path.name)

            self.protected_vault.add_documents(
                ids=chunk_ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(
                "Inserted %d confidential chunk(s) into protected_vault "
                "(deleted %d previous chunk(s)).",
                len(chunks),
                vault_deleted,
            )

        logger.info(
            "Successfully inserted %d new chunk(s) for '%s' (classification='%s', document_type='%s') into collection '%s' (deleted %d previous chunk(s)).",
            len(chunks),
            path.name,
            classification,
            document_type,
            self.vector_store.collection_name,
            deleted_count,
        )

        return {
            "status": "success",
            "file_name": path.name,
            "classification": classification,
            "document_type": document_type,
            "chunks": len(chunks),
            "collection": self.vector_store.collection_name,
        }

    def ingest_directory(self, directory: str | Path) -> dict[str, Any]:
        """Recursively scan a directory for supported documents (.pdf, .docx) and perform bulk ingestion.

        Workflow:
        Recursive scan -> Filter supported extensions -> Invoke single document ingest() -> Aggregate statistics

        Args:
            directory (str | Path): Path to root documents directory.

        Returns:
            dict[str, Any]: Aggregated bulk ingestion summary statistics.

        Raises:
            FileNotFoundError: If the directory does not exist.
            ValueError: If the path is not a directory.
        """
        dir_path = Path(directory)
        logger.info("Starting bulk ingestion from directory: '%s'...", dir_path)

        if not dir_path.exists():
            logger.error("Bulk ingestion target directory not found: '%s'", dir_path)
            raise FileNotFoundError(f"Target documents directory not found at path: '{dir_path}'")

        if not dir_path.is_dir():
            logger.error("Bulk ingestion path is not a directory: '%s'", dir_path)
            raise ValueError(f"Target path is not a directory: '{dir_path}'")

        start_time = time.perf_counter()

        # Discover all PDF and DOCX files recursively
        target_files = [
            f for f in dir_path.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        logger.info("Starting bulk ingestion...")
        logger.info("Discovered %d supported document(s) in '%s'.", len(target_files), dir_path)

        documents_processed = 0
        public_documents = 0
        confidential_documents = 0
        total_chunks = 0
        failures: list[dict[str, str]] = []

        for file_item in target_files:
            logger.info("Processing: %s", file_item.name)
            try:
                result = self.ingest(file_item)
                documents_processed += 1
                total_chunks += result.get("chunks", 0)

                classification = str(result.get("classification", "")).lower()
                if classification == "public":
                    public_documents += 1
                elif classification == "confidential":
                    confidential_documents += 1

            except Exception as exc:
                logger.error("Failed to ingest document '%s': %s", file_item.name, exc)
                failures.append({
                    "file": file_item.name,
                    "reason": str(exc),
                })

        elapsed_seconds = round(time.perf_counter() - start_time, 2)

        logger.info("Completed.")
        logger.info("Documents processed: %d", documents_processed)
        logger.info("Total chunks: %d", total_chunks)
        logger.info("Time taken: %.1f sec", elapsed_seconds)

        status_label = "success" if not failures else ("partial_success" if documents_processed > 0 else "failed")

        return {
            "status": status_label,
            "documents_processed": documents_processed,
            "public_documents": public_documents,
            "confidential_documents": confidential_documents,
            "total_chunks": total_chunks,
            "failed_documents": len(failures),
            "failures": failures,
            "processing_time_seconds": elapsed_seconds,
        }
