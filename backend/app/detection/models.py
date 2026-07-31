"""Data models and dataclasses for SentinelAI Enterprise Semantic DLP Detection system."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SensitiveItem:
    """Represents a structured sensitive information item identified by DLP evaluation."""

    type: str  # e.g. "DATABASE_CREDENTIAL", "API_KEY", "INTERNAL_HOSTNAME"
    value: str  # e.g. "admin_enterprise / Sentinel@Secure2026"

    def to_dict(self, redact: bool = False) -> dict[str, Any]:
        """Convert sensitive item to dictionary with optional value redaction for public API serialization.

        Args:
            redact (bool): If True, replaces actual cleartext secret value with '[REDACTED]'.
        """
        if redact:
            return {
                "type": self.type,
                "value": "[REDACTED]",
                "redacted": True,
            }
        return {
            "type": self.type,
            "value": self.value,
            "redacted": False,
        }


@dataclass
class SimilarityResult:
    """Dataclass holding vector embedding candidate retrieval results."""

    similarity: float
    distance: float
    risk: str
    matched_document: str | None = None
    matched_chunk: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    classification: str | None = None
    sensitivity: str | None = None
    document_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result dataclass to dictionary."""
        return asdict(self)


@dataclass
class OverlapResult:
    """Dataclass holding LLM enterprise DLP factual overlap evaluation results."""

    decision: str  # "ALLOW" or "BLOCK"
    confidence: float
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    information_type: str = ""
    category: str = "OTHER"
    categories: list[str] = field(default_factory=list)
    sensitive_items: list[SensitiveItem] = field(default_factory=list)
    reason: str = ""
    policy_violation: bool = False

    @property
    def overlap(self) -> bool:
        """Helper property indicating if a policy violation was detected.

        Derived from PolicyEngine evaluation, not from LLM classification.
        """
        return self.policy_violation

    def to_dict(self, redact_sensitive_items: bool = False) -> dict[str, Any]:
        """Convert result dataclass to dictionary."""
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "severity": self.severity,
            "information_type": self.information_type,
            "category": self.category,
            "categories": self.categories,
            "sensitive_items": [item.to_dict(redact=redact_sensitive_items) for item in self.sensitive_items],
            "reason": self.reason,
            "policy_violation": self.policy_violation,
            "overlap": self.overlap,
        }


@dataclass
class LeakDetectionResult:
    """Dataclass holding complete Enterprise Semantic DLP decision payload."""

    decision: str  # "ALLOW" or "BLOCK"
    blocked: bool
    similarity: float
    risk: str
    overlap: bool
    confidence: float
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    categories: list[str] = field(default_factory=list)
    sensitive_items: list[SensitiveItem] = field(default_factory=list)
    reason: str = ""
    policy_violation: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    matched_document: str | None = None
    matched_chunk: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    replacement_response: str | None = None

    @classmethod
    def create_utc_timestamp(cls) -> str:
        """Generate ISO 8601 UTC timestamp string."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(
        self,
        include_internal: bool = False,
        expose_sensitive_values: bool = False,
        expose_document_names: bool = False,
    ) -> dict[str, Any]:
        """Convert result dataclass to dictionary for JSON serialization.

        Args:
            include_internal (bool): If True, includes internal matched_chunk for server auditing logs.
                                     If False (default), omits matched_chunk to prevent API data leakage.
            expose_sensitive_values (bool): If False (default), redacts cleartext secret values in sensitive_items.
            expose_document_names (bool): If False (default), masks matched_document as 'Protected Document'.

        Returns:
            dict[str, Any]: Serialized leak detection payload.
        """
        redact_secrets = not expose_sensitive_values
        serialized_items = [item.to_dict(redact=redact_secrets) for item in self.sensitive_items]

        doc_name = self.matched_document
        if not expose_document_names and doc_name:
            doc_name = "Protected Document"

        payload = {
            "decision": self.decision,
            "blocked": self.blocked,
            "similarity": self.similarity,
            "risk": self.risk,
            "overlap": self.overlap,
            "confidence": self.confidence,
            "severity": self.severity,
            "categories": self.categories,
            "sensitive_items": serialized_items,
            "reason": self.reason,
            "policy_violation": self.policy_violation,
            "timestamp": self.timestamp,
            "matched_document": doc_name,
            "metadata": self.metadata,
            "replacement_response": self.replacement_response,
        }
        if include_internal:
            payload["matched_chunk"] = self.matched_chunk
        return payload

    def to_public_dict(
        self,
        expose_sensitive_values: bool = False,
        expose_document_names: bool = False,
    ) -> dict[str, Any]:
        """Explicit helper returning safe public serialization with redacted secret values and masked doc names."""
        return self.to_dict(
            include_internal=False,
            expose_sensitive_values=expose_sensitive_values,
            expose_document_names=expose_document_names,
        )
