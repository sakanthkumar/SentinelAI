import os
from pathlib import Path
from typing import Callable
import docx
from pypdf import PdfReader


class DocumentLoader:
    """Extracts raw text content from supported enterprise document formats.

    Currently supports PDF and DOCX files. Easily extensible for future formats.
    """

    def __init__(self) -> None:
        """Initialize the loader with supported extension mappings."""
        self._loaders: dict[str, Callable[[Path], str]] = {
            ".pdf": self._load_pdf,
            ".docx": self._load_docx,
        }

    def load(self, file_path: str | Path) -> str:
        """Load and extract text from the given file path.

        Args:
            file_path (str | Path): Path to the target document.

        Returns:
            str: Extracted raw text content.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or the extracted text is empty.
            RuntimeError: If file parsing fails.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found at path: '{path}'")

        if not path.is_file():
            raise ValueError(f"Specified path is not a valid file: '{path}'")

        extension = path.suffix.lower()
        if extension not in self._loaders:
            supported = ", ".join(self._loaders.keys())
            raise ValueError(
                f"Unsupported file format '{extension}'. Supported formats: {supported}"
            )

        loader_func = self._loaders[extension]
        try:
            extracted_text = loader_func(path)
        except Exception as exc:
            raise RuntimeError(f"Failed to read file '{path.name}': {exc}") from exc

        cleaned_text = extracted_text.strip()
        if not cleaned_text:
            raise ValueError(f"Extracted document content is empty for file: '{path.name}'")

        return cleaned_text

    def _load_pdf(self, path: Path) -> str:
        """Extract text from a PDF file using PyPDF."""
        reader = PdfReader(path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)

    def _load_docx(self, path: Path) -> str:
        """Extract text from a DOCX file using python-docx."""
        doc = docx.Document(path)
        text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
        return "\n".join(text_parts)
