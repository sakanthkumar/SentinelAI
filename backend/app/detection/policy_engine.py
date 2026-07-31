"""Enterprise Policy Engine Module for SentinelAI DLP Platform."""

import logging
from typing import Any

from app.detection.config_loader import ConfigLoader
from app.detection.models import OverlapResult

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Enforces enterprise security policies, category blocking rules, and document sensitivity controls."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize PolicyEngine loading policies from ConfigLoader."""
        self.config_loader = config_loader or ConfigLoader()
        self.policy_config = self.config_loader.load_dlp_policy()
        self.security_levels = self.config_loader.load_security_levels().get("sensitivity_levels", {})

        self.blocked_categories = set(self.policy_config.get("blocked_categories", []))
        self.allowed_categories = set(self.policy_config.get("allowed_categories", []))
        self.confidence_threshold = float(self.policy_config.get("confidence_threshold", 0.80))
        self.default_replacement_message = str(
            self.policy_config.get("default_replacement_message", "Response blocked due to enterprise security policy.")
        )

        logger.info(
            "PolicyEngine initialized (%d blocked categories, confidence_threshold=%.2f).",
            len(self.blocked_categories),
            self.confidence_threshold,
        )

    def format_policy_for_prompt(self) -> str:
        """Format configured enterprise policy rules into text for prompt template injection."""
        blocked_str = ", ".join(sorted(self.blocked_categories))
        return (
            f"Blocked Sensitive Categories: [{blocked_str}]\n"
            f"Allowed General Categories: [GENERAL_INFORMATION, HR_POLICY, SECURITY_POLICY, OTHER]\n"
            f"Strictness Threshold: Confidence >= {self.confidence_threshold:.2f} requires blocking blocked categories."
        )

    def evaluate_policy(
        self,
        overlap_result: OverlapResult,
        sensitivity: str = "CONFIDENTIAL",
    ) -> dict[str, Any]:
        """Evaluate LLM semantic classification against enterprise security policy rules.

        The LLM provides ONLY the information category and confidence.
        This engine is the SOLE decision-maker for ALLOW or BLOCK.

        Decision logic:
            1. If the classified category is in blocked_categories AND confidence >= threshold → BLOCK.
            2. If the document sensitivity is SECRET and category is blocked → BLOCK (regardless of confidence).
            3. Otherwise → ALLOW.

        Args:
            overlap_result (OverlapResult): Semantic classification from FactualOverlapDetector.
            sensitivity (str): Sensitivity level of matched document.

        Returns:
            dict[str, Any]: Policy enforcement result with decision, blocked, severity, and replacement_response.
        """
        sensitivity_upper = sensitivity.upper() if sensitivity else "CONFIDENTIAL"

        # Check for blocked category matches
        matching_blocked_categories = [
            cat for cat in overlap_result.categories if cat in self.blocked_categories
        ]

        # Determine policy violation: ONLY based on category + confidence + sensitivity
        is_policy_violation = bool(matching_blocked_categories)

        should_block = (
            is_policy_violation
            and overlap_result.confidence >= self.confidence_threshold
        ) or (
            sensitivity_upper == "SECRET"
            and is_policy_violation
        )

        # Calculate final severity rating
        if should_block:
            if sensitivity_upper in {"SECRET", "RESTRICTED"} or "PASSWORD" in matching_blocked_categories or "PRIVATE_KEY" in matching_blocked_categories:
                final_severity = "CRITICAL"
            elif overlap_result.severity in {"HIGH", "CRITICAL"}:
                final_severity = overlap_result.severity
            else:
                final_severity = "HIGH"
        else:
            final_severity = overlap_result.severity if overlap_result.severity else "LOW"

        decision = "BLOCK" if should_block else "ALLOW"
        replacement_message = self.default_replacement_message if should_block else None

        # Update the overlap_result with PolicyEngine's decision
        overlap_result.decision = decision
        overlap_result.policy_violation = is_policy_violation and should_block

        logger.info(
            "PolicyEngine evaluation complete: decision='%s', sensitivity='%s', matching_blocked=%s, confidence=%.2f, severity='%s'.",
            decision,
            sensitivity_upper,
            matching_blocked_categories,
            overlap_result.confidence,
            final_severity,
        )

        return {
            "decision": decision,
            "blocked": should_block,
            "severity": final_severity,
            "policy_violation": is_policy_violation and should_block,
            "replacement_response": replacement_message,
        }
