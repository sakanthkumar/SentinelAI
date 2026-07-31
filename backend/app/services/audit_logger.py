"""Thread-safe Security Audit Logging Service for SentinelAI Platform.

Persists security evaluation logs (exfiltration attempts, policy violations, allowed RAG queries)
to persistent backend storage and provides real-time telemetry metrics.
"""

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any

from app.llm.config import settings

logger = logging.getLogger(__name__)


class SecurityAuditLogger:
    """Enterprise Security Audit Logger managing persistent event recording and analytics."""

    def __init__(self, log_path: str | Path | None = None) -> None:
        """Initialize SecurityAuditLogger with thread-safe file persistence.

        Args:
            log_path (str | Path | None): Optional custom file path for audit events JSON.
        """
        if log_path:
            self.log_file = Path(log_path).resolve()
        else:
            base_dir = Path(__file__).resolve().parents[2]
            self.log_file = base_dir / "storage" / "audit_events.json"

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

        # Ensure storage file exists as valid JSON array
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f)

        logger.info("Initialized SecurityAuditLogger at '%s'.", str(self.log_file))

    def _read_events_unlocked(self) -> list[dict[str, Any]]:
        """Internal helper to read events array from disk."""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as exc:
            logger.error("Failed to read audit log file '%s': %s", self.log_file, exc)
        return []

    def log_event(
        self,
        question: str,
        decision: str,
        severity: str,
        categories: list[str],
        reason: str,
        matched_document: str | None = None,
        confidence: float = 0.0,
        policy_violation: bool = False,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Record a new security audit evaluation event.

        Args:
            question (str): Original user prompt question.
            decision (str): Security decision ('ALLOW' or 'BLOCK').
            severity (str): Threat severity ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
            categories (list[str]): Data categories detected.
            reason (str): Policy engine rationale summary.
            matched_document (str | None): Reference document matched in vault if any.
            confidence (float): Overlap / risk confidence score.
            policy_violation (bool): Whether event constitutes enterprise policy violation.
            timestamp (str | None): UTC ISO timestamp string.

        Returns:
            dict[str, Any]: Formatted security audit event object.
        """
        import uuid
        from datetime import datetime, timezone

        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        utc_now = timestamp or datetime.now(timezone.utc).isoformat()

        event: dict[str, Any] = {
            "id": event_id,
            "timestamp": utc_now,
            "question": question,
            "decision": decision.upper(),
            "severity": severity.upper(),
            "categories": categories or ["GENERAL_INFORMATION"],
            "matchedDocument": matched_document or "N/A",
            "reason": reason,
            "policyViolation": policy_violation,
            "confidence": round(float(confidence), 4),
        }

        with self._lock:
            events = self._read_events_unlocked()
            events.insert(0, event)  # newest first
            # Keep up to 1000 recent security audit events
            if len(events) > 1000:
                events = events[:1000]

            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2)
                logger.info("Recorded security audit event %s (%s - %s)", event_id, decision, severity)
            except Exception as exc:
                logger.error("Failed to write audit event %s to file: %s", event_id, exc)

        return event

    def get_events(
        self,
        limit: int = 50,
        decision: str | None = None,
        severity: str | None = None,
        search_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve filtered security audit events.

        Args:
            limit (int): Maximum events to return.
            decision (str | None): Filter by 'ALLOW' or 'BLOCK'.
            severity (str | None): Filter by severity.
            search_query (str | None): Substring search across question, reason, or categories.

        Returns:
            list[dict[str, Any]]: List of matching security audit events.
        """
        with self._lock:
            events = self._read_events_unlocked()

        filtered = []
        for evt in events:
            if decision and decision.upper() != "ALL" and evt.get("decision") != decision.upper():
                continue
            if severity and severity.upper() != "ALL" and evt.get("severity") != severity.upper():
                continue
            if search_query and search_query.strip():
                q = search_query.strip().lower()
                q_text = str(evt.get("question", "")).lower()
                r_text = str(evt.get("reason", "")).lower()
                cats = [str(c).lower() for c in evt.get("categories", [])]
                if q not in q_text and q not in r_text and not any(q in c for c in cats):
                    continue
            filtered.append(evt)

        return filtered[:limit]

    def get_stats(self) -> dict[str, int]:
        """Compute aggregated security metrics across all logged events.

        Returns:
            dict[str, int]: Dictionary containing blocked_requests, allowed_requests, and total_events counts.
        """
        with self._lock:
            events = self._read_events_unlocked()

        blocked = sum(1 for e in events if e.get("decision") == "BLOCK")
        allowed = sum(1 for e in events if e.get("decision") == "ALLOW")

        return {
            "blocked_requests": blocked,
            "allowed_requests": allowed,
            "total_events": len(events),
        }
