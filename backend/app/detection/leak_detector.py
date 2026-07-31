"""LeakDetector Decision Engine Module for SentinelAI Enterprise Semantic DLP Detection.

Coordinates SimilarityDetector (candidate retrieval), FactualOverlapDetector (DLP reasoning),
and PolicyEngine (policy evaluation) to evaluate whether a query context or response is safe.
"""

import logging
from typing import Any

from app.detection.factual_overlap_detector import FactualOverlapDetector
from app.detection.models import LeakDetectionResult
from app.detection.policy_engine import PolicyEngine
from app.detection.similarity_detector import SimilarityDetector

logger = logging.getLogger(__name__)


class LeakDetector:
    """Enterprise Semantic DLP Orchestration Engine connecting retrieval, LLM analysis, and PolicyEngine."""

    def __init__(
        self,
        similarity_detector: SimilarityDetector | None = None,
        factual_overlap_detector: FactualOverlapDetector | None = None,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        """Initialize LeakDetector with injected components."""
        self.similarity_detector = similarity_detector or SimilarityDetector()
        self.factual_overlap_detector = factual_overlap_detector or FactualOverlapDetector()
        self.policy_engine = policy_engine or PolicyEngine()

        logger.info("LeakDetector initialized with SimilarityDetector, FactualOverlapDetector, and PolicyEngine.")

    def evaluate_context(
        self,
        question: str,
        context_documents: list[dict[str, Any]],
    ) -> LeakDetectionResult:
        """Perform pre-generation DLP context analysis on user query and retrieved document chunks.

        If user query asks for sensitive credentials, PII, or confidential secrets, this pre-generation
        check catches exfiltration prior to LLM response synthesis, preventing data exposure and saving latency.
        """
        if not question or not question.strip():
            question_text = "General information query"
        else:
            question_text = question.strip()

        timestamp = LeakDetectionResult.create_utc_timestamp()

        # Combine question with context text for candidate screening
        context_samples = []
        for doc in context_documents[:3]:
            txt = doc.get("content") or doc.get("text") or doc.get("metadata", {}).get("text", "")
            if txt:
                context_samples.append(txt)
        context_text_sample = "\n".join(context_samples)
        combined_text = f"User Question: {question_text}\nContext Sample: {context_text_sample[:500]}"

        # 1. Candidate Retrieval: Vector embedding search against protected_vault
        try:
            sim_result = self.similarity_detector.detect_similarity(combined_text)
        except Exception as exc:
            logger.error("SimilarityDetector pre-generation check failed: %s", exc)
            return self.evaluate_response(question_text)

        # 2. No confidential reference chunk found -> Safe to proceed
        if not sim_result.matched_chunk:
            return LeakDetectionResult(
                decision="ALLOW",
                blocked=False,
                similarity=sim_result.similarity,
                risk=sim_result.risk,
                overlap=False,
                confidence=0.0,
                severity="LOW",
                categories=["GENERAL_INFORMATION"],
                sensitive_items=[],
                reason="No confidential reference document matched.",
                policy_violation=False,
                timestamp=timestamp,
                matched_document=None,
                matched_chunk=None,
                metadata={},
                replacement_response=None,
            )

        doc_sensitivity = (sim_result.sensitivity or sim_result.classification or "CONFIDENTIAL").upper()

        # 3. Confidential reference chunk matched -> Execute DLP Reasoning
        try:
            overlap_result = self.factual_overlap_detector.detect_overlap(
                response=question_text,
                matched_chunk=sim_result.matched_chunk,
                classification=sim_result.classification,
                sensitivity=doc_sensitivity,
                document_type=sim_result.document_type,
                source=sim_result.matched_document,
                user_query=question_text,  # Pass user question so the LLM has correct context
            )
        except Exception as exc:
            logger.error("FactualOverlapDetector pre-generation DLP evaluation failed: %s", exc)
            return self.evaluate_response(question_text)

        # 4. Evaluate Security Policy
        policy_eval = self.policy_engine.evaluate_policy(
            overlap_result=overlap_result,
            sensitivity=doc_sensitivity,
        )

        return LeakDetectionResult(
            decision=policy_eval["decision"],
            blocked=policy_eval["blocked"],
            similarity=sim_result.similarity,
            risk=sim_result.risk,
            overlap=overlap_result.overlap,
            confidence=overlap_result.confidence,
            severity=policy_eval["severity"],
            categories=overlap_result.categories,
            sensitive_items=overlap_result.sensitive_items,
            reason=overlap_result.reason,
            policy_violation=policy_eval["policy_violation"],
            timestamp=timestamp,
            matched_document=sim_result.matched_document,
            matched_chunk=sim_result.matched_chunk,
            metadata=sim_result.metadata,
            replacement_response=policy_eval["replacement_response"],
        )

    def evaluate_response(self, response: str, user_query: str | None = None) -> LeakDetectionResult:
        """Evaluate an LLM-generated response for data exfiltration against Enterprise DLP policy."""
        if not response or not response.strip():
            logger.warning("Rejected leak detection request: empty response text.")
            raise ValueError("Response text cannot be empty or whitespace.")

        clean_response = response.strip()
        timestamp = LeakDetectionResult.create_utc_timestamp()

        logger.info(
            "\n"
            "==========================\n"
            "USER QUESTION\n"
            "==========================\n"
            "%s",
            user_query or "(no user query provided)",
        )

        logger.info("Executing Enterprise Semantic DLP decision pipeline at UTC %s...", timestamp)

        # 1. Candidate Retrieval: Vector embedding search against protected_vault
        try:
            sim_result = self.similarity_detector.detect_similarity(clean_response)
        except Exception as exc:
            logger.error("SimilarityDetector candidate retrieval failed: %s", exc)
            raise RuntimeError(f"LeakDetector failed during candidate retrieval: {exc}") from exc

        # 2. No confidential reference chunk found -> Safe to allow immediately
        if not sim_result.matched_chunk:
            logger.info(
                "\n"
                "==========================\n"
                "SIMILARITY RESULT\n"
                "==========================\n"
                "similarity   : %.4f\n"
                "risk         : %s\n"
                "matched_doc  : None (below threshold — ALLOW immediately)",
                sim_result.similarity,
                sim_result.risk,
            )
            return LeakDetectionResult(
                decision="ALLOW",
                blocked=False,
                similarity=sim_result.similarity,
                risk=sim_result.risk,
                overlap=False,
                confidence=0.0,
                severity="LOW",
                categories=["GENERAL_INFORMATION"],
                sensitive_items=[],
                reason="No confidential reference document matched.",
                policy_violation=False,
                timestamp=timestamp,
                matched_document=None,
                matched_chunk=None,
                metadata={},
                replacement_response=None,
            )

        doc_sensitivity = (sim_result.sensitivity or sim_result.classification or "CONFIDENTIAL").upper()
        logger.info(
            "\n"
            "==========================\n"
            "RETRIEVED CHUNK\n"
            "==========================\n"
            "source       : %s\n"
            "similarity   : %.4f\n"
            "risk         : %s\n"
            "sensitivity  : %s\n"
            "doc_type     : %s\n"
            "chunk (first 300 chars):\n%s",
            sim_result.matched_document,
            sim_result.similarity,
            sim_result.risk,
            doc_sensitivity,
            sim_result.document_type,
            (sim_result.matched_chunk or "")[:300],
        )

        # 3. Candidate reference chunk found -> Execute DLP Reasoning via FactualOverlapDetector
        try:
            overlap_result = self.factual_overlap_detector.detect_overlap(
                response=clean_response,
                matched_chunk=sim_result.matched_chunk,
                classification=sim_result.classification,
                sensitivity=doc_sensitivity,
                document_type=sim_result.document_type,
                source=sim_result.matched_document,
                user_query=user_query,
            )
        except Exception as exc:
            logger.error("FactualOverlapDetector DLP evaluation failed: %s", exc)
            raise RuntimeError(f"LeakDetector failed during DLP evaluation: {exc}") from exc

        # 4. Evaluate Security Policy via PolicyEngine
        policy_eval = self.policy_engine.evaluate_policy(
            overlap_result=overlap_result,
            sensitivity=doc_sensitivity,
        )

        final_decision = policy_eval["decision"]
        is_blocked = policy_eval["blocked"]
        final_severity = policy_eval["severity"]
        is_policy_violation = policy_eval["policy_violation"]
        replacement_msg = policy_eval["replacement_response"]

        logger.info(
            "\n"
            "==========================\n"
            "LLM DLP OUTPUT\n"
            "==========================\n"
            "Decision    : %s\n"
            "Categories  : %s\n"
            "Confidence  : %.2f\n"
            "Severity    : %s\n"
            "Reason      : %s",
            overlap_result.decision,
            overlap_result.categories,
            overlap_result.confidence,
            overlap_result.severity,
            overlap_result.reason,
        )

        matching_blocked = [cat for cat in overlap_result.categories if cat in self.policy_engine.blocked_categories]
        logger.info(
            "\n"
            "==========================\n"
            "POLICY ENGINE\n"
            "==========================\n"
            "Blocked Categories    : %s\n"
            "Matched Categories    : %s\n"
            "Confidence Threshold  : %.2f\n"
            "Final Decision        : %s",
            matching_blocked,
            overlap_result.categories,
            self.policy_engine.confidence_threshold,
            final_decision,
        )

        if is_blocked:
            logger.warning(
                "BLOCK Decision enforced by PolicyEngine: categories=%s, severity='%s', confidence=%.2f for source '%s'.",
                overlap_result.categories,
                final_severity,
                overlap_result.confidence,
                sim_result.matched_document,
            )
        else:
            logger.info(
                "ALLOW Decision approved by PolicyEngine: categories=%s, severity='%s', confidence=%.2f.",
                overlap_result.categories,
                final_severity,
                overlap_result.confidence,
            )

        return LeakDetectionResult(
            decision=final_decision,
            blocked=is_blocked,
            similarity=sim_result.similarity,
            risk=sim_result.risk,
            overlap=overlap_result.overlap,
            confidence=overlap_result.confidence,
            severity=final_severity,
            categories=overlap_result.categories,
            sensitive_items=overlap_result.sensitive_items,
            reason=overlap_result.reason,
            policy_violation=is_policy_violation,
            timestamp=timestamp,
            matched_document=sim_result.matched_document,
            matched_chunk=sim_result.matched_chunk,
            metadata=sim_result.metadata,
            replacement_response=replacement_msg,
        )
