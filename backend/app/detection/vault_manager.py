"""Vault Manager Module for SentinelAI Semantic Exfiltration Detection.

Manages protected reference documents in a dedicated ChromaDB collection ('protected_vault')
used exclusively for semantic leak detection reference storage.
"""

import logging
from pathlib import Path
from typing import Any

from app.services.chunking import TextChunker
from app.services.document_loader import DocumentLoader
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_VAULT_COLLECTION = "protected_vault"
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class VaultManager:
    """Manages indexing, deduplication, and vector storage for protected vault reference documents."""

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        chunker: TextChunker | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
        vault_collection_name: str = DEFAULT_VAULT_COLLECTION,
    ) -> None:
        """Initialize VaultManager with optional injected dependencies.

        Args:
            loader (DocumentLoader | None): Document loading component.
            chunker (TextChunker | None): Text splitting component.
            embedding_service (EmbeddingService | None): Vector embedding component.
            vector_store (VectorStore | None): Vector store component bound to the vault collection.
            vault_collection_name (str): Dedicated ChromaDB collection name ('protected_vault').
        """
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or TextChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vault_collection_name = vault_collection_name
        self.vector_store = vector_store or VectorStore(collection_name=self.vault_collection_name)

        logger.info(
            "VaultManager initialized for collection '%s'.",
            self.vault_collection_name,
        )

    def index_document(self, file_path: str | Path) -> dict[str, Any]:
        """Index a single protected reference document into the vault.

        Workflow:
        1. Validate file path & extension
        2. Load document text (DocumentLoader)
        3. Split text into chunks (TextChunker)
        4. Delete existing vectors for source document (VectorStore.delete_documents_by_source)
        5. Generate vector embeddings (EmbeddingService)
        6. Persist vectors with deterministic IDs ({filename}_{index}) and minimal metadata

        Args:
            file_path (str | Path): Path to the protected reference document.

        Returns:
            dict[str, Any]: Indexing summary dictionary.

        Raises:
            FileNotFoundError: If the document file does not exist.
            ValueError: If the file path is invalid, empty, or an unsupported file format.
            RuntimeError: If document loading, chunking, embedding generation, or vector persistence fails.
        """
        path = Path(file_path)
        logger.info("Starting vault indexing for document: '%s'", path.name)

        if not path.exists():
            logger.error("Protected document file not found: '%s'", path)
            raise FileNotFoundError(f"Protected document not found at path: '{path}'")

        if not path.is_file():
            logger.error("Specified path is not a valid file: '%s'", path)
            raise ValueError(f"Specified path is not a file: '{path}'")

        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            logger.error("Unsupported file extension '%s' for document '%s'", extension, path.name)
            raise ValueError(
                f"Unsupported file format '{extension}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        filename = path.name

        # 1. Document Loading
        logger.info("Loading protected document text from '%s'...", filename)
        try:
            raw_text = self.loader.load(path)
        except Exception as exc:
            logger.error("Failed to load text from document '%s': %s", filename, exc)
            raise RuntimeError(f"Document loading failed for '{filename}': {exc}") from exc

        # 2. Text Chunking
        logger.info("Splitting text content for '%s' into manageable chunks...", filename)
        try:
            chunks = self.chunker.split_text(raw_text)
            logger.info("Generated %d text chunk(s) for document '%s'.", len(chunks), filename)
        except Exception as exc:
            logger.error("Failed to split text for document '%s': %s", filename, exc)
            raise RuntimeError(f"Text chunking failed for '{filename}': {exc}") from exc

        # 3. Duplicate Deletion
        logger.info(
            "Checking for existing vectors for '%s' in collection '%s'...",
            filename,
            self.vault_collection_name,
        )
        try:
            deleted_count = self.vector_store.delete_documents_by_source(filename)
            if deleted_count > 0:
                logger.info(
                    "Duplicate deletion complete: Removed %d existing vector(s) for '%s'.",
                    deleted_count,
                    filename,
                )
            else:
                logger.info(
                    "No existing vectors found for '%s'. Proceeding with fresh indexing.",
                    filename,
                )
        except Exception as exc:
            logger.error("Failed duplicate deletion for document '%s': %s", filename, exc)
            raise RuntimeError(f"Duplicate vector cleanup failed for '{filename}': {exc}") from exc

        # 4. Embedding Generation
        logger.info("Generating vector embeddings for %d chunk(s) of '%s'...", len(chunks), filename)
        try:
            embeddings = self.embedding_service.embed_documents(chunks)
            logger.info("Generated %d vector embedding(s) for document '%s'.", len(embeddings), filename)
        except Exception as exc:
            logger.error("Failed to generate embeddings for document '%s': %s", filename, exc)
            raise RuntimeError(f"Embedding generation failed for '{filename}': {exc}") from exc

        # 5. Deterministic Chunk IDs & Minimal Metadata Construction
        doc_prefix = path.stem

        chunk_ids = [
            f"{doc_prefix}_{idx}"
            for idx in range(len(chunks))
        ]
        metadatas = [
            {
                "source": filename,
                "chunk_index": idx,
                "vault": True,
            }
            for idx in range(len(chunks))
        ]

        # 6. Vector Persistence
        logger.info(
            "Storing %d chunk(s) into ChromaDB collection '%s'...",
            len(chunk_ids),
            self.vault_collection_name,
        )
        try:
            self.vector_store.add_documents(
                ids=chunk_ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as exc:
            logger.error("Failed to persist vectors for document '%s': %s", filename, exc)
            raise RuntimeError(f"Vector persistence failed for '{filename}': {exc}") from exc

        logger.info(
            "Vault indexing complete for '%s': %d chunk(s) inserted into '%s' (deleted %d previous).",
            filename,
            len(chunks),
            self.vault_collection_name,
            deleted_count,
        )

        return {
            "status": "success",
            "file_name": filename,
            "chunks_indexed": len(chunks),
            "chunks_deleted": deleted_count,
            "collection": self.vault_collection_name,
        }

    def index_directory(self, directory_path: str | Path) -> dict[str, Any]:
        """Recursively scan and index all supported protected documents within a directory into the vault.

        Args:
            directory_path (str | Path): Path to directory containing protected documents.

        Returns:
            dict[str, Any]: Aggregated directory indexing summary statistics.

        Raises:
            FileNotFoundError: If the directory path does not exist.
            ValueError: If the path is not a directory.
        """
        dir_path = Path(directory_path)
        logger.info("Starting directory indexing for vault path: '%s'", dir_path)

        if not dir_path.exists():
            logger.error("Vault directory not found: '%s'", dir_path)
            raise FileNotFoundError(f"Vault directory not found at path: '{dir_path}'")

        if not dir_path.is_dir():
            logger.error("Specified path is not a directory: '%s'", dir_path)
            raise ValueError(f"Specified path is not a directory: '{dir_path}'")

        target_files = [
            f for f in dir_path.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        logger.info(
            "Discovered %d supported document(s) in vault directory '%s'.",
            len(target_files),
            dir_path,
        )

        processed_count = 0
        total_chunks_indexed = 0
        total_chunks_deleted = 0
        failed_files: list[dict[str, str]] = []

        for file_item in target_files:
            try:
                result = self.index_document(file_item)
                processed_count += 1
                total_chunks_indexed += result.get("chunks_indexed", 0)
                total_chunks_deleted += result.get("chunks_deleted", 0)
            except Exception as exc:
                logger.error("Failed to index file '%s' during directory scan: %s", file_item.name, exc)
                failed_files.append({"file_name": file_item.name, "error": str(exc)})

        logger.info(
            "Directory indexing complete for '%s': %d/%d file(s) indexed (%d total chunks inserted, %d chunks deleted).",
            dir_path,
            processed_count,
            len(target_files),
            total_chunks_indexed,
            total_chunks_deleted,
        )

        return {
            "status": "success",
            "directory": str(dir_path.resolve()),
            "total_files_discovered": len(target_files),
            "total_files_processed": processed_count,
            "total_chunks_indexed": total_chunks_indexed,
            "total_chunks_deleted": total_chunks_deleted,
            "failed_files": failed_files,
            "collection": self.vault_collection_name,
        }

    def get_collection_name(self) -> str:
        """Return the ChromaDB collection name used for the protected vault.

        Returns:
            str: Collection name ('protected_vault').
        """
        return self.vault_collection_name
    def get_vector_store(self) -> VectorStore:
        """Returns the protected vault vector store."""
        return self.vector_store