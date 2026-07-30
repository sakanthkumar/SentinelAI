import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextChunker:
    """Splits raw text into manageable, semantic chunks for embedding and vector storage."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """Initialize the TextChunker.

        Args:
            chunk_size (int): Maximum character length per chunk. Defaults to 1000.
            chunk_overlap (int): Character overlap between consecutive chunks. Defaults to 200.

        Raises:
            ValueError: If chunk parameters are non-positive or overlap >= chunk_size.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def split_text(self, text: str) -> list[str]:
        """Split document text into ordered non-empty chunks.

        Args:
            text (str): Extracted raw text content.

        Returns:
            list[str]: Filtered list of non-empty text chunks preserving sequence order.

        Raises:
            ValueError: If input text is empty or blank.
        """
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty or whitespace-only text.")

        raw_chunks = self._splitter.split_text(text)

        # Filter empty chunks while preserving original order
        chunks = [c.strip() for c in raw_chunks if c and c.strip()]

        if not chunks:
            raise ValueError("Text splitting resulted in zero valid chunks.")

        logger.info(
            "Successfully split text into %d chunks (chunk_size=%d, overlap=%d).",
            len(chunks),
            self.chunk_size,
            self.chunk_overlap,
        )
        return chunks
