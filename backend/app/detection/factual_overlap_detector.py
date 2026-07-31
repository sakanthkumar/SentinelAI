"""Factual Overlap & Enterprise Semantic DLP Detector Module for SentinelAI.

Acts as an Enterprise Data Loss Prevention (DLP) Security Officer evaluating whether an LLM
response exposes sensitive credentials, PII, secrets, or proprietary knowledge contained in
a protected vault reference chunk.
"""

import json
import logging
import re
from typing import Any

from app.detection.config_loader import ConfigLoader, PromptTemplateLoader
from app.detection.models import OverlapResult, SensitiveItem
from app.detection.policy_engine import PolicyEngine
from app.llm.base import BaseLLM
from app.llm.factory import LLMFactory

logger = logging.getLogger(__name__)

SUPPORTED_CATEGORIES = {
    "PASSWORD", "DATABASE_CREDENTIAL", "API_KEY", "TOKEN", "SECRET",
    "SSH_KEY", "PRIVATE_KEY", "CONNECTION_STRING", "INTERNAL_HOSTNAME",
    "INTERNAL_IP", "CUSTOMER_PII", "EMPLOYEE_PII", "PAYROLL_DATA", "FINANCIAL_DATA",
    "TRADE_SECRET", "PROPRIETARY_ALGORITHM", "BUSINESS_PLAN",
    "GENERAL_INFORMATION", "HR_POLICY", "SECURITY_POLICY", "OTHER"
}


class FactualOverlapDetector:
    """Enterprise Data Loss Prevention (DLP) Security Officer evaluating response exfiltration risk via LLM reasoning."""

    def __init__(
        self,
        llm: BaseLLM | None = None,
        template_loader: PromptTemplateLoader | None = None,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        """Initialize FactualOverlapDetector with injected LLM and template loader."""
        self.llm = llm or LLMFactory.get_provider()
        self.template_loader = template_loader or PromptTemplateLoader()
        self.policy_engine = policy_engine or PolicyEngine()
        logger.info("FactualOverlapDetector initialized with LLM provider '%s'.", type(self.llm).__name__)

    def detect_overlap(
        self,
        response: str,
        matched_chunk: str,
        classification: str | None = None,
        sensitivity: str | None = None,
        document_type: str | None = None,
        source: str | None = None,
        user_query: str | None = None,
    ) -> OverlapResult:
        """Evaluate whether the generated response exposes sensitive information from a protected vault chunk.

        Args:
            response (str): Generated LLM response text to evaluate.
            matched_chunk (str): Protected vault reference chunk text.
            classification (str | None): Document classification ('public' or 'confidential').
            sensitivity (str | None): Document sensitivity ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'SECRET').
            document_type (str | None): Inferred document type (e.g., 'financial', 'credentials').
            source (str | None): Source document filename.
            user_query (str | None): Original user question query.

        Returns:
            OverlapResult: Typed DLP evaluation result containing decision, categories, sensitive_items, and reasoning.
        """
        if not response or not response.strip():
            raise ValueError("Response text cannot be empty or whitespace.")

        if not matched_chunk or not matched_chunk.strip():
            raise ValueError("Matched vault chunk text cannot be empty or whitespace.")

        clean_response = response.strip()
        clean_chunk = matched_chunk.strip()
        doc_classification = classification or "confidential"
        doc_sensitivity = (sensitivity or "CONFIDENTIAL").upper()
        doc_type = document_type or "general"
        doc_source = source or "unknown"
        query_text = user_query or "General inquiry"

        enterprise_policy_str = self.policy_engine.format_policy_for_prompt()

        # Render prompts from template files
        system_prompt = self.template_loader.render_system_prompt(
            classification=doc_classification,
            sensitivity=doc_sensitivity,
            document_type=doc_type,
            source=doc_source,
            enterprise_policy=enterprise_policy_str,
        )

        user_prompt = self.template_loader.render_user_prompt(
            matched_chunk=clean_chunk,
            response=clean_response,
            sensitivity=doc_sensitivity,
            user_query=query_text,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw_llm_output = self.llm.generate(
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
        except Exception as exc:
            logger.error("LLM execution failed during DLP evaluation: %s", exc)
            raise RuntimeError(f"DLP LLM evaluation failed: {exc}") from exc

        if not raw_llm_output or not raw_llm_output.strip():
            raise RuntimeError("LLM returned an empty response during DLP evaluation.")

        return self._parse_json_response(raw_llm_output)

    def _parse_json_response(self, raw_text: str) -> OverlapResult:
        """Parse raw LLM response into OverlapResult with multi-category and structured sensitive_items support."""
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return self._sanitize_overlap_dict(data)
        except json.JSONDecodeError as err:
            logger.warning("Failed standard JSON parsing: %s. Attempting regex extraction...", err)

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return self._sanitize_overlap_dict(data)
            except Exception as exc:
                logger.error("Regex JSON extraction fallback failed: %s", exc)

        logger.error("Could not parse valid JSON from LLM DLP response: '%s'", raw_text)
        return OverlapResult(
            decision="ALLOW",
            confidence=0.0,
            severity="LOW",
            categories=["OTHER"],
            sensitive_items=[],
            reason="Failed to parse valid JSON DLP evaluation output from LLM provider.",
            policy_violation=False,
        )

    def _sanitize_overlap_dict(self, data: dict[str, Any]) -> OverlapResult:
        """Sanitize and validate LLM classification output.

        The LLM is a semantic classifier only — it returns category, confidence,
        severity, reason, and sensitive_items. It does NOT return a decision or
        policy_violation. Those are determined by PolicyEngine.
        """
        raw_conf = data.get("confidence", 0.0)
        try:
            confidence = max(0.0, min(1.0, float(raw_conf)))
        except (ValueError, TypeError):
            confidence = 0.0

        raw_severity = str(data.get("severity", "")).strip().upper()
        severity = raw_severity if raw_severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "LOW"

        info_type = str(data.get("information_type", "")).strip()
        single_cat = str(data.get("category", "")).strip().upper()

        # Parse multiple categories
        raw_categories = data.get("categories", [])
        if isinstance(raw_categories, str):
            raw_categories = [raw_categories]
        elif not isinstance(raw_categories, list):
            raw_categories = []

        if single_cat and single_cat not in raw_categories:
            raw_categories.insert(0, single_cat)

        categories = [
            cat.strip().upper() for cat in raw_categories
            if isinstance(cat, str) and cat.strip().upper() in SUPPORTED_CATEGORIES
        ]
        if not categories:
            categories = [single_cat] if single_cat in SUPPORTED_CATEGORIES else ["GENERAL_INFORMATION"]

        if not single_cat or single_cat not in SUPPORTED_CATEGORIES:
            single_cat = categories[0]

        if not info_type:
            info_type = single_cat.replace("_", " ").title()

        # Parse structured sensitive items
        raw_items = data.get("sensitive_items", [])
        sensitive_items: list[SensitiveItem] = []
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    item_type = str(item.get("type", single_cat)).strip().upper()
                    item_val = str(item.get("value", "")).strip()
                    if item_val:
                        sensitive_items.append(SensitiveItem(type=item_type, value=item_val))
                elif isinstance(item, str) and item.strip():
                    sensitive_items.append(SensitiveItem(type=categories[0], value=item.strip()))

        reason = str(data.get("reason", "")).strip() or "No explanation provided."

        # LLM is a classifier only — decision and policy_violation are set by PolicyEngine
        return OverlapResult(
            decision="PENDING",
            confidence=confidence,
            severity=severity,
            information_type=info_type,
            category=single_cat,
            categories=categories,
            sensitive_items=sensitive_items,
            reason=reason,
            policy_violation=False,
        )
