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

    Combines semantic document retrieval with pre-generation security inspection using LeakDetector
    and PolicyEngine evaluation to prevent data exfiltration.
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

    def _validate_question(self, question: str) -> None:
        """Validate question input string."""
        if not question or not question.strip():
            raise ValueError("Question string cannot be empty or whitespace.")

    def _build_context(self, documents: list[dict[str, Any]]) -> str:
        """Build formatted context block from retrieved document objects."""
        context_parts = []
        for idx, doc in enumerate(documents, start=1):
            metadata = doc.get("metadata", {})
            text = doc.get("content") or doc.get("text") or metadata.get("text") or ""
            source = metadata.get("source") or doc.get("source") or "Unknown Document"
            context_parts.append(f"--- Document Chunk {idx} (Source: {source}) ---\n{text}")
        return "\n\n".join(context_parts)

    def _build_prompt(self, context: str, question: str) -> str:
        """Construct grounded prompt template."""
        return (
            f"DOCUMENT CONTEXT:\n{context}\n\n"
            f"USER QUESTION:\n{question}\n\n"
            f"INSTRUCTIONS:\n"
            f"Answer the user's question using ONLY the provided Document Context above. "
            f"If the information is not present in the context, state clearly that it is unavailable."
        )

    def _sanitize_sources(
        self,
        documents: list[dict[str, Any]],
        is_blocked: bool = False,
    ) -> list[dict[str, Any]]:
        """Sanitize document metadata and redact cleartext source content for public response."""
        sanitized = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            source_name = metadata.get("source") or doc.get("source") or "Unknown Document"
            classification = (metadata.get("classification") or doc.get("classification") or "public").lower()
            raw_text = doc.get("content") or doc.get("text") or metadata.get("text") or ""

            if is_blocked and self.sanitize_sources_on_block:
                display_name = "Protected Document" if not self.expose_document_names else source_name
                sanitized.append({
                    "source": display_name,
                    "classification": classification,
                    "text": "[BLOCKED - SECURITY POLICY VIOLATION]",
                })
            else:
                display_name = source_name if (self.expose_document_names or classification == "public") else "Protected Document"
                sanitized.append({
                    "source": display_name,
                    "classification": classification,
                    "text": raw_text,
                })
        return sanitized

    def _audit_log(
        self,
        question: str,
        answer: str,
        documents: list[dict[str, Any]],
        leak_report: LeakDetectionResult,
    ) -> None:
        """Extension point writing thread-safe security audit log events."""
        pass

    def ask(self, question: str, top_k: int = 5) -> dict[str, Any]:
        """Execute RAG question-answering workflow with pre-generation leak detection and security redaction.

        Workflow:
            Validate Question -> Retrieve Chunks -> Pre-Generation Context DLP Analysis
            -> If BLOCK: Return Security Message Immediately
            -> If ALLOW: Build Prompt -> Generate LLM Answer -> Redact Secrets -> Return Response
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

        # 2. Pre-Generation DLP Analysis on User Query & Retrieved Context
        try:
            leak_report: LeakDetectionResult = self.leak_detector.evaluate_context(
                question=question,
                context_documents=raw_documents,
            )
        except Exception as exc:
            logger.error("Pre-generation DLP evaluation failed: %s. Falling back...", exc)
            leak_report = None

        # 3. If Pre-Generation check BLOCKS -> Return Security Message Immediately (bypassing LLM generation)
        if leak_report and leak_report.blocked:
            logger.warning("Query BLOCKED during pre-generation DLP context analysis.")
            final_answer = leak_report.replacement_response or "Access Blocked: The requested information violates enterprise security policy."
            final_sources = self._sanitize_sources(raw_documents, is_blocked=True)
            self._audit_log(question, final_answer, raw_documents, leak_report)

            serialized_leak = leak_report.to_dict(
                include_internal=(self.security_mode == "DEVELOPMENT"),
                expose_sensitive_values=self.expose_sensitive_values,
                expose_document_names=self.expose_document_names,
            )

            return {
                "question": question,
                "answer": final_answer,
                "sources": final_sources,
                "retrieved_documents": len(raw_documents),
                "security_evaluation": serialized_leak,
            }

        # 4. Pre-generation check ALLOWS -> Build Prompt & Generate LLM Answer
        context = self._build_context(raw_documents)
        prompt = self._build_prompt(context=context, question=question)

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
            raise RuntimeError(f"RAGPipeline failed during LLM generation: {exc}") from exc

        if not answer or not answer.strip():
            raise RuntimeError("LLM generated an empty response.")

        cleaned_answer = answer.strip()

        # 5. Secondary Post-Generation DLP check on synthesized answer text
        try:
            post_leak_report: LeakDetectionResult = self.leak_detector.evaluate_response(cleaned_answer, user_query=question)
        except Exception as exc:
            logger.error("Post-generation DLP evaluation failed: %s", exc)
            post_leak_report = leak_report or LeakDetectionResult(
                decision="ALLOW", blocked=False, similarity=0.0, risk="LOW", overlap=False,
                confidence=0.0, severity="LOW", categories=["GENERAL_INFORMATION"]
            )

        if post_leak_report.blocked:
            final_answer = post_leak_report.replacement_response or "Access Blocked: The requested information violates enterprise security policy."
            final_sources = self._sanitize_sources(raw_documents, is_blocked=True)
        else:
            final_answer = cleaned_answer
            final_sources = self._sanitize_sources(raw_documents, is_blocked=False)

        self._audit_log(question, final_answer, raw_documents, post_leak_report)

        serialized_leak = post_leak_report.to_dict(
            include_internal=(self.security_mode == "DEVELOPMENT"),
            expose_sensitive_values=self.expose_sensitive_values,
            expose_document_names=self.expose_document_names,
        )

        return {
            "question": question,
            "answer": final_answer,
            "sources": final_sources,
            "retrieved_documents": len(raw_documents),
            "security_evaluation": serialized_leak,
        }
