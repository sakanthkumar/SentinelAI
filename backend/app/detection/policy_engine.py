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
            f"Allowed General Categories: [GENERAL_INFORMATION, SECURITY_POLICY, OTHER]\n"
            f"Strictness Threshold: Confidence >= {self.confidence_threshold:.2f} requires blocking blocked categories."
        )

    def evaluate_policy(
        self,
        overlap_result: OverlapResult,
        sensitivity: str = "CONFIDENTIAL",
    ) -> dict[str, Any]:
        """Evaluate LLM overlap analysis against enterprise security policy rules.

        Args:
            overlap_result (OverlapResult): Raw DLP analysis from FactualOverlapDetector.
            sensitivity (str): Sensitivity level of matched document ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'SECRET').

        Returns:
            dict[str, Any]: Policy enforcement result with decision, blocked, severity, and replacement_response.
        """
        sensitivity_upper = sensitivity.upper() if sensitivity else "CONFIDENTIAL"
        level_info = self.security_levels.get(sensitivity_upper, {"strictness": "HIGH", "default_policy": "EVALUATE"})

        # Check for blocked category matches
        matching_blocked_categories = [
            cat for cat in overlap_result.categories if cat in self.blocked_categories
        ]

        # Determine policy violation & blocking decision
        is_policy_violation = (
            overlap_result.policy_violation
            or bool(matching_blocked_categories)
            or (overlap_result.overlap and overlap_result.decision == "BLOCK")
            or (sensitivity_upper == "SECRET" and overlap_result.overlap)
        )

        should_block = (
            is_policy_violation
            and overlap_result.confidence >= self.confidence_threshold
        ) or (sensitivity_upper == "SECRET" and overlap_result.overlap)

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

        logger.info(
            "PolicyEngine evaluation complete: decision='%s', sensitivity='%s', matching_blocked=%s, severity='%s'.",
            decision,
            sensitivity_upper,
            matching_blocked_categories,
            final_severity,
        )

        return {
            "decision": decision,
            "blocked": should_block,
            "severity": final_severity,
            "policy_violation": is_policy_violation,
            "replacement_response": replacement_message,
        }
