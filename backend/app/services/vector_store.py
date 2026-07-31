import logging
from pathlib import Path
from typing import Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.llm.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages document chunk persistence and similarity searching using ChromaDB."""

    def __init__(
        self,
        collection_name: str = "enterprise_docs",
        persist_directory: str | Path | None = None,
    ) -> None:
        """Initialize ChromaDB persistent client and collection.

        Args:
            collection_name (str): Name of the ChromaDB collection. Defaults to 'enterprise_docs'.
            persist_directory (str | Path | None): Local directory path for persistent storage.

        Raises:
            RuntimeError: If initializing ChromaDB client or collection fails.
        """
        self.collection_name = collection_name
        target_dir = persist_directory or settings.chroma_db_path
        persist_path = Path(target_dir).resolve()
        persist_path.mkdir(parents=True, exist_ok=True)
        self.persist_directory = str(persist_path)

        try:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "Initialized ChromaDB collection '%s' at '%s'.",
                self.collection_name,
                self.persist_directory,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize ChromaDB collection '{collection_name}': {exc}"
            ) from exc

    def delete_documents_by_source(self, source: str) -> int:
        """Delete all existing vector embeddings belonging to a specific source document.

        Args:
            source (str): Source document file name (e.g., 'employee_handbook.pdf').

        Returns:
            int: Number of deleted document chunks.

        Raises:
            ValueError: If source file name is empty or blank.
            RuntimeError: If vector store deletion fails.
        """
        if not source or not source.strip():
            raise ValueError("Source file name cannot be empty.")

        try:
            existing = self._collection.get(where={"source": source})
            existing_ids = existing.get("ids", []) if existing else []
            deleted_count = len(existing_ids)

            if deleted_count > 0:
                self._collection.delete(where={"source": source})
                logger.info(
                    "Existing vectors removed: Deleted %d previous chunk(s) for source '%s' from collection '%s'.",
                    deleted_count,
                    source,
                    self.collection_name,
                )
            else:
                logger.info(
                    "No existing vectors found for source document '%s' in collection '%s'.",
                    source,
                    self.collection_name,
                )

            return deleted_count
        except Exception as exc:
            raise RuntimeError(
                f"Failed to delete existing vectors for source document '{source}': {exc}"
            ) from exc

    def delete_documents_by_document_id(self, document_id: str, source: str | None = None) -> int:
        """Delete vector embeddings by document_id metadata filter, falling back to source.

        Args:
            document_id (str): Unique document identifier.
            source (str | None): Optional source filename fallback.

        Returns:
            int: Total count of deleted vector chunk embeddings.
        """
        if not document_id or not document_id.strip():
            raise ValueError("document_id cannot be empty.")

        deleted_count = 0
        try:
            # 1. Try deleting by document_id metadata
            by_id = self._collection.get(where={"document_id": document_id})
            ids_to_del = by_id.get("ids", []) if by_id else []
            if ids_to_del:
                self._collection.delete(where={"document_id": document_id})
                deleted_count += len(ids_to_del)

            # 2. Fallback to source filename if provided and no IDs matched by document_id
            if deleted_count == 0 and source and source.strip():
                by_source = self._collection.get(where={"source": source.strip()})
                ids_to_del_source = by_source.get("ids", []) if by_source else []
                if ids_to_del_source:
                    self._collection.delete(where={"source": source.strip()})
                    deleted_count += len(ids_to_del_source)

            logger.info(
                "Deleted %d vector chunk(s) for document_id '%s' (source='%s') from collection '%s'.",
                deleted_count,
                document_id,
                source,
                self.collection_name,
            )
            return deleted_count
        except Exception as exc:
            raise RuntimeError(
                f"Failed to delete vectors for document_id '{document_id}' in collection '{self.collection_name}': {exc}"
            ) from exc

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add document chunks and vector embeddings to the collection.

        Args:
            ids (list[str]): Unique identifiers for each chunk.
            documents (list[str]): Raw text chunk strings.
            embeddings (list[list[float]]): Vector embeddings corresponding to documents.
            metadatas (list[dict[str, Any]] | None): Optional metadata dictionaries per chunk.

        Raises:
            ValueError: If input lists are empty or mismatched in length.
            RuntimeError: If database insertion fails.
        """
        if not ids or not documents or not embeddings:
            raise ValueError("ids, documents, and embeddings cannot be empty.")

        if not (len(ids) == len(documents) == len(embeddings)):
            raise ValueError("Mismatched lengths between ids, documents, and embeddings.")

        try:
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("Added %d document chunks to ChromaDB collection '%s'.", len(ids), self.collection_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to store documents in ChromaDB collection '{self.collection_name}': {exc}"
            ) from exc

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform similarity search using a query vector embedding.

        Args:
            query_embedding (list[float]): Vector embedding of the query.
            top_k (int): Number of top matching documents to return. Defaults to 4.
            where (dict[str, Any] | None): Optional metadata filtering dictionary for ChromaDB.

        Returns:
            list[dict[str, Any]]: List of results containing id, document content, distance, and metadata.

        Raises:
            ValueError: If query_embedding is empty or top_k is non-positive.
            RuntimeError: If query execution fails.
        """
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        try:
            query_params: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                query_params["where"] = where

            results = self._collection.query(**query_params)

            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for idx in range(len(results["ids"][0])):
                    formatted_results.append(
                        {
                            "id": results["ids"][0][idx],
                            "document": results["documents"][0][idx] if results["documents"] else "",
                            "distance": results["distances"][0][idx] if results["distances"] else 0.0,
                            "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                        }
                    )
            return formatted_results
        except Exception as exc:
            raise RuntimeError(f"Similarity search failed in collection '{self.collection_name}': {exc}") from exc
