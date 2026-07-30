"""RAGPipeline Orchestration Module for SentinelAI Platform."""

import logging
from typing import Any

from app.ai.retriever import Retriever
from app.detection.config_loader import ConfigLoader
from app.detection.leak_detector import LeakDetector
from app.detection.models import LeakDetectionResult
from app.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates the Retrieval-Augmented Generation (RAG) workflow with integrated leak detection.

    Combines semantic document retrieval with LLM generation and post-generation security
    inspection using LeakDetector to prevent data exfiltration.
    """

    def __init__(
        self,
        retriever: Retriever,
        llm: BaseLLM,
        leak_detector: LeakDetector | None = None,
        config_loader: ConfigLoader | None = None,
    ) -> None:
        """Initialize the RAG pipeline with injected dependencies and security configuration.

        Args:
            retriever (Retriever): Injected document retriever instance.
            llm (BaseLLM): Injected provider-agnostic LLM instance.
            leak_detector (LeakDetector | None): Injected leak detector decision engine. Defaults to LeakDetector().
            config_loader (ConfigLoader | None): Injected configuration loader instance. Defaults to ConfigLoader().

        Raises:
            ValueError: If required retriever or llm dependencies are missing.
        """
        if not retriever:
            raise ValueError("Retriever instance is required for RAGPipeline.")
        if not llm:
            raise ValueError("BaseLLM instance is required for RAGPipeline.")

        self.retriever = retriever
        self.llm = llm
        self.leak_detector = leak_detector or LeakDetector()
        self.config_loader = config_loader or ConfigLoader()

        self.security_config = self.config_loader.load_security_config()
        self.security_mode = str(self.security_config.get("security_mode", "PRODUCTION")).upper()
        self.expose_confidential_sources = bool(self.security_config.get("expose_confidential_sources", False))
        self.expose_document_names = bool(self.security_config.get("expose_document_names", False))
        self.expose_sensitive_values = bool(self.security_config.get("expose_sensitive_values", False))
        self.sanitize_sources_on_block = bool(self.security_config.get("sanitize_sources_on_block", True))

        logger.info(
            "RAGPipeline initialized (security_mode='%s', expose_sensitive_values=%s, expose_document_names=%s).",
            self.security_mode,
            self.expose_sensitive_values,
            self.expose_document_names,
        )

    def ask(self, question: str, top_k: int = 5) -> dict[str, Any]:
        """Execute RAG question-answering workflow with post-generation leak detection and security redaction.

        Workflow:
            Validate Question -> Retrieve Chunks -> Build Context -> Build Prompt -> Generate Answer
            -> LeakDetector Evaluation -> Enforce Security Decision -> Sanitize Sources & Redact Secrets -> Return Results

        Args:
            question (str): User question string.
            top_k (int): Number of context chunks to retrieve. Defaults to 5.

        Returns:
            dict[str, Any]: Structured dictionary response containing question, answer, sanitized sources,
                            retrieved_documents count, and redacted leak_detection payload.

        Raises:
            ValueError: If question is empty or retrieval yields zero documents.
            RuntimeError: If retriever, LLM execution, or leak detection fails.
        """
        self._validate_question(question)

        logger.info("RAGPipeline processing question: '%s' (top_k=%d)", question, top_k)

        # 1. Retrieve top-k relevant document chunks from vector database
        try:
            retrieval_output = self.retriever.retrieve(query=question, top_k=top_k)
        except Exception as exc:
            raise RuntimeError(f"RAGPipeline failed during document retrieval: {exc}") from exc

        raw_documents = retrieval_output.get("documents", [])
        if not raw_documents:
            raise ValueError(
                "No relevant document context found. Cannot generate grounded response."
            )

        # 2. Build structured context block from retrieved documents
        context = self._build_context(raw_documents)

        # 3. Construct grounded prompt enforcing context compliance
        prompt = self._build_prompt(context=context, question=question)

        # 4. Generate answer using injected LLM provider
        messages = [
            {
                "role": "system",
                "content": (
                    "You are SentinelAI, an enterprise AI assistant. "
                    "Answer ONLY using the supplied document context. "
                    "If the answer is not present in the context, clearly state that "
                    "the information is unavailable in the provided documentation."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            answer = self.llm.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
        except Exception as exc:
            raise RuntimeError(
                f"RAGPipeline failed during LLM generation: {exc}"
            ) from exc

        if not answer or not answer.strip():
            raise RuntimeError("LLM generated an empty response.")

        cleaned_answer = answer.strip()

        # 5. Evaluate generated response using injected LeakDetector
        try:
            leak_report: LeakDetectionResult = self.leak_detector.evaluate_response(cleaned_answer)
        except Exception as exc:
            logger.error("RAGPipeline leak detection evaluation failed: %s", exc)
            raise RuntimeError(f"RAGPipeline failed during leak detection evaluation: {exc}") from exc

        # Internal Audit Logging (includes raw unredacted secret count, matched_document, and matched_chunk)
        logger.info(
            "Leak detection summary at UTC %s: similarity=%.4f, risk='%s', overlap=%s, confidence=%.2f, decision='%s', matched_doc='%s', sensitive_items_count=%d.",
            leak_report.timestamp,
            leak_report.similarity,
            leak_report.risk,
            leak_report.overlap,
            leak_report.confidence,
            leak_report.decision,
            leak_report.matched_document,
            len(leak_report.sensitive_items),
        )

        # 6. Enforce security decision & sanitize sources
        if leak_report.blocked:
            logger.warning("RAG answer blocked by LeakDetector due to security policy.")
            final_answer = leak_report.replacement_response or "Response blocked due to enterprise security policy."
            final_sources = self._sanitize_sources(raw_documents, is_blocked=True)
        else:
            final_answer = cleaned_answer
            final_sources = self._sanitize_sources(raw_documents, is_blocked=False)

        # Extension Points: Response Firewall inspection & Audit logging
        final_answer = self._inspect_response(final_answer)
        self._audit_log(question, final_answer, raw_documents, leak_report)

        logger.info("RAGPipeline execution complete with decision '%s'.", leak_report.decision)

        # Secure public serialization: omits matched_chunk, redacts sensitive values, masks doc names if configured
        serialized_leak_detection = leak_report.to_dict(
            include_internal=(self.security_mode == "DEVELOPMENT"),
            expose_sensitive_values=self.expose_sensitive_values,
            expose_document_names=self.expose_document_names,
        )

        return {
            "question": question,
            "answer": final_answer,
            "sources": final_sources,
            "retrieved_documents": len(raw_documents),
            "leak_detection": serialized_leak_detection,
        }

    def _sanitize_sources(
        self, documents: list[dict[str, Any]], is_blocked: bool
    ) -> list[dict[str, Any]]:
        """Sanitize source document representations for public API responses.

        Enforces mask rules for source filenames and strips content text on BLOCK.

        Args:
            documents (list[dict[str, Any]]): Raw retrieved document chunks.
            is_blocked (bool): True if DLP decision was BLOCK.

        Returns:
            list[dict[str, Any]]: Sanitized source dictionaries.
        """
        sanitized = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            raw_source = metadata.get("source") or doc.get("source", "unknown")
            classification = metadata.get("classification") or doc.get("classification", "confidential")
            doc_type = metadata.get("document_type") or doc.get("document_type", "general")

            source_name = raw_source if self.expose_document_names else "Protected Document"

            item: dict[str, Any] = {
                "source": source_name,
                "classification": classification,
                "document_type": doc_type,
            }

            # Include content text ONLY in DEVELOPMENT mode or if expose_confidential_sources is True and NOT blocked
            if self.expose_confidential_sources and not (is_blocked and self.sanitize_sources_on_block):
                item["content"] = doc.get("content", "")

            sanitized.append(item)

        return sanitized

    def _validate_question(self, question: str) -> None:
        """Validate input question."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty or whitespace.")

    def _build_context(self, documents: list[dict[str, Any]]) -> str:
        """Format retrieved document chunks into a clean context string."""
        context_parts = []
        for idx, doc in enumerate(documents, start=1):
            content = doc.get("content", "").strip()
            if content:
                context_parts.append(f"Document {idx}:\n{content}")
        return "\n\n".join(context_parts)

    def _build_prompt(self, context: str, question: str) -> str:
        """Construct prompt grounding the LLM strictly to provided context."""
        return (
            "You are an enterprise AI assistant for SentinelAI.\n"
            "Use ONLY the provided document context to answer the user's question.\n"
            "Do not invent information or rely on unmentioned facts.\n"
            "If the answer cannot be found in the supplied context, "
            "respond that the information is unavailable in the provided documentation.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )

    def _inspect_response(self, response: str) -> str:
        """Pipeline Extension Point: Response Firewall inspection / safety filtering."""
        return response

    def _audit_log(
        self,
        question: str,
        response: str,
        sources: list[dict[str, Any]],
        leak_report: LeakDetectionResult,
    ) -> None:
        """Pipeline Extension Point: Audit Logging for enterprise compliance."""
        pass
