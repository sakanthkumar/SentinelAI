import logging
from typing import Any

from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant document chunks from the vector database based on semantic similarity.

    Follows Clean Architecture and SOLID principles. Depends on injected EmbeddingService
    and VectorStore instances without coupling to specific implementations or LLM components.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the Retriever with injected services.

        Args:
            embedding_service (EmbeddingService): Service used to embed search queries.
            vector_store (VectorStore): Persistent vector store interface for retrieval.

        Raises:
            ValueError: If required dependencies are missing.
        """
        if not embedding_service:
            raise ValueError("EmbeddingService instance is required.")
        if not vector_store:
            raise ValueError("VectorStore instance is required.")

        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform semantic retrieval for a user query.

        Workflow:
            Validate Query -> Generate Embedding -> Search Vector Store -> Apply Filters -> Return Results

        Args:
            query (str): The search query text.
            top_k (int): Maximum number of relevant document chunks to return. Defaults to 5.
            filters (dict[str, Any] | None): Optional metadata filter dict for ChromaDB.

        Returns:
            dict[str, Any]: Structured retrieval output with format:
                {
                    "query": str,
                    "documents": [
                        {
                            "content": str,
                            "metadata": dict,
                            "score": float
                        }
                    ],
                    "count": int
                }

        Raises:
            ValueError: If query is empty or invalid parameters are provided.
            RuntimeError: If embedding generation or vector search fails.
        """
        self._validate_input(query, top_k)

        logger.info("Executing retrieval for query: '%s' (top_k=%d)", query, top_k)

        # 1. Prepare/preprocess query & metadata filters (Extension Point: Authorization / Cache check)
        effective_filters = self._build_filters(filters)

        # 2. Generate vector embedding for query
        try:
            query_embedding = self.embedding_service.embed_text(query)
        except Exception as exc:
            raise RuntimeError(f"Retrieval failed during query embedding: {exc}") from exc

        # 3. Perform vector database similarity search (Extension Point: Hybrid / BM25 Search)
        try:
            raw_results = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k,
                where=effective_filters,
            )
        except Exception as exc:
            raise RuntimeError(f"Retrieval failed during vector search: {exc}") from exc

        # 4. Format and process retrieved results (Extension Point: Reranking / Score Normalization)
        documents = self._format_results(raw_results)

        logger.info("Retrieved %d relevant documents for query.", len(documents))

        return {
            "query": query,
            "documents": documents,
            "count": len(documents),
        }

    def _validate_input(self, query: str, top_k: int) -> None:
        """Validate search input parameters."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

    def _build_filters(self, filters: dict[str, Any] | None) -> dict[str, Any] | None:
        """Build and merge metadata filter criteria.

        Extension Point: Modify/append user permission, tenant, or timestamp filters here.
        """
        if not filters:
            return None
        return filters

    def _format_results(self, raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format and score raw vector search hits into standardized document dictionaries.

        Extension Point: Plug in Reranking, BM25 fusion scores, or threshold filtering here.
        """
        formatted = []
        for item in raw_results:
            raw_distance = item.get("distance", 0.0)
            # Cosine distance to similarity conversion (bounded 0.0 - 1.0)
            similarity_score = max(0.0, round(1.0 - raw_distance, 4))

            formatted.append(
                {
                    "content": item.get("document", ""),
                    "metadata": item.get("metadata", {}),
                    "score": similarity_score,
                }
            )
        return formatted
