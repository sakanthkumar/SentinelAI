"""Embedding Similarity Detector Module for SentinelAI Semantic Exfiltration Detection.

Retrieves semantically candidate reference documents from the 'protected_vault' ChromaDB
collection using vector embeddings for downstream Enterprise Semantic DLP analysis.
"""

import logging

from app.detection.models import SimilarityResult
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_VAULT_COLLECTION = "protected_vault"
DEFAULT_HIGH_THRESHOLD = 0.70
DEFAULT_MEDIUM_THRESHOLD = 0.55


class SimilarityDetector:
    """Retrieves vector candidate reference chunks from protected vault collection for DLP reasoning."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        medium_threshold: float = DEFAULT_MEDIUM_THRESHOLD,
        vault_collection_name: str = DEFAULT_VAULT_COLLECTION,
    ) -> None:
        """Initialize SimilarityDetector with optional injected dependencies.

        Args:
            embedding_service (EmbeddingService | None): Injected embedding service instance.
            vector_store (VectorStore | None): Injected vector store bound to 'protected_vault'.
            high_threshold (float): Similarity indicator threshold for HIGH score label (default 0.70).
            medium_threshold (float): Similarity indicator threshold for MEDIUM score label (default 0.55).
            vault_collection_name (str): Dedicated ChromaDB collection name ('protected_vault').
        """
        if high_threshold <= medium_threshold:
            raise ValueError("high_threshold must be strictly greater than medium_threshold.")

        self.embedding_service = embedding_service or EmbeddingService()
        self.vault_collection_name = vault_collection_name
        self.vector_store = vector_store or VectorStore(collection_name=self.vault_collection_name)
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

        logger.info(
            "SimilarityDetector initialized for vault collection '%s'.",
            self.vault_collection_name,
        )

    def detect_similarity(self, response: str) -> SimilarityResult:
        """Embed an LLM response and retrieve the top candidate reference chunk from protected_vault.

        Args:
            response (str): The generated LLM response text to inspect.

        Returns:
            SimilarityResult: Candidate match containing similarity metric, matched chunk text, and metadata.

        Raises:
            ValueError: If response text is empty or whitespace.
            RuntimeError: If embedding generation or vector search fails.
        """
        if not response or not response.strip():
            logger.warning("Rejected similarity detection request: empty response string.")
            raise ValueError("Response text cannot be empty or whitespace.")

        clean_response = response.strip()
        logger.info("Executing embedding candidate search against vault collection '%s'...", self.vault_collection_name)

        # 1. Generate query embedding for LLM response
        try:
            response_embedding = self.embedding_service.embed_text(clean_response)
        except Exception as exc:
            logger.error("Failed to generate embedding for response: %s", exc)
            raise RuntimeError(f"Similarity candidate search embedding generation failed: {exc}") from exc

        # 2. Search ONLY the protected_vault collection for the top matching chunk (top_k=1)
        try:
            hits = self.vector_store.similarity_search(
                query_embedding=response_embedding,
                top_k=1,
            )
        except Exception as exc:
            logger.error("Failed vector search against collection '%s': %s", self.vault_collection_name, exc)
            raise RuntimeError(f"Similarity candidate vector search failed: {exc}") from exc

        # Handle case where protected_vault is empty or zero matches returned
        if not hits:
            logger.info("No matching vectors found in protected vault.")
            return SimilarityResult(
                similarity=0.0,
                distance=1.0,
                risk="LOW",
                matched_document=None,
                matched_chunk=None,
                metadata={},
                classification=None,
                document_type=None,
            )

        top_hit = hits[0]
        raw_distance = float(top_hit.get("distance", 0.0))
        similarity_score = max(0.0, round(1.0 - raw_distance, 4))

        metadata = top_hit.get("metadata", {})
        matched_document = metadata.get("source", "unknown")
        matched_chunk = top_hit.get("document", "")
        classification = metadata.get("classification", "confidential")
        document_type = metadata.get("document_type", "general")

        risk_level = self._evaluate_risk(similarity_score)

        result = SimilarityResult(
            similarity=similarity_score,
            distance=round(raw_distance, 4),
            risk=risk_level,
            matched_document=matched_document,
            matched_chunk=matched_chunk,
            metadata=metadata,
            classification=classification,
            document_type=document_type,
        )

        logger.info(
            "Candidate retrieval complete: score=%.4f (distance=%.4f), matched_doc='%s', classification='%s', doc_type='%s'.",
            result.similarity,
            result.distance,
            result.matched_document,
            result.classification,
            result.document_type,
        )

        return result

    def _evaluate_risk(self, similarity: float) -> str:
        """Classify candidate score indicator for logging context."""
        if similarity >= self.high_threshold:
            return "HIGH"
        elif similarity >= self.medium_threshold:
            return "MEDIUM"
        return "LOW"
