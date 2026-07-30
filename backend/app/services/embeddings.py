import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates vector embeddings for text chunks using SentenceTransformers.

    Loads the underlying embedding model once during initialization to avoid overhead.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize and load the SentenceTransformer model.

        Args:
            model_name (str): HuggingFace model identifier. Defaults to 'all-MiniLM-L6-v2'.

        Raises:
            RuntimeError: If model loading fails.
        """
        self.model_name = model_name
        try:
            logger.info("Loading embedding model '%s'...", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model '%s' loaded successfully.", self.model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load SentenceTransformer model '{self.model_name}': {exc}"
            ) from exc

    def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a single text string.

        Args:
            text (str): Input text string.

        Returns:
            list[float]: Vector embedding as a list of floating point numbers.

        Raises:
            ValueError: If input text is empty.
            RuntimeError: If vector generation fails.
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty or blank text.")

        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as exc:
            raise RuntimeError(f"Failed to generate embedding for text: {exc}") from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of text strings.

        Args:
            texts (list[str]): List of text strings to embed.

        Returns:
            list[list[float]]: List of vector embeddings.

        Raises:
            ValueError: If texts list is empty.
            RuntimeError: If batch vector generation fails.
        """
        if not texts:
            raise ValueError("Texts list cannot be empty.")

        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True, batch_size=32)
            return embeddings.tolist()
        except Exception as exc:
            raise RuntimeError(f"Failed batch embedding generation: {exc}") from exc
