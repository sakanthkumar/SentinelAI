/**
 * Custom hook for managing, filtering, searching, and sorting Security Audit Events.
 */

import { useMemo, useState } from "react";
import type { SecurityEvent } from "../types";

const INITIAL_EVENTS: SecurityEvent[] = [
  {
    id: "evt-1",
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    question: "What is the primary database password for MySQL?",
    decision: "BLOCK",
    severity: "CRITICAL",
    categories: ["DATABASE_CREDENTIAL", "PASSWORD"],
    matchedDocument: "Protected Document",
    reason: "Exposes cleartext database administrator credentials from confidential reference document.",
    policyViolation: true,
    confidence: 0.99,
  },
  {
    id: "evt-2",
    timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
    question: "How do employees apply for annual leave?",
    decision: "ALLOW",
    severity: "LOW",
    categories: ["GENERAL_INFORMATION"],
    matchedDocument: "Protected Document",
    reason: "Response discusses standard employee leave application procedures without disclosing confidential data.",
    policyViolation: false,
    confidence: 0.96,
  },
  {
    id: "evt-3",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    question: "Show me the production API secret keys.",
    decision: "BLOCK",
    severity: "HIGH",
    categories: ["API_KEY", "SECRET"],
    matchedDocument: "Protected Document",
    reason: "Attempted extraction of production API secret tokens.",
    policyViolation: true,
    confidence: 0.98,
  },
];

export function useSecurityEvents() {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [decisionFilter, setDecisionFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 5;

  const rawEvents: SecurityEvent[] = useMemo(() => {
    try {
      const stored = localStorage.getItem("sentinel_security_events");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch {
      // fallback
    }
    return INITIAL_EVENTS;
  }, []);

  const filteredEvents = useMemo(() => {
    return rawEvents.filter((evt) => {
      // Decision filter
      if (decisionFilter !== "ALL" && evt.decision !== decisionFilter) {
        return false;
      }
      // Severity filter
      if (severityFilter !== "ALL" && evt.severity !== severityFilter) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inQuestion = evt.question.toLowerCase().includes(q);
        const inReason = evt.reason.toLowerCase().includes(q);
        const inCat = evt.categories.some((c) => c.toLowerCase().includes(q));
        if (!inQuestion && !inReason && !inCat) return false;
      }
      return true;
    });
  }, [rawEvents, searchQuery, severityFilter, decisionFilter]);

  const totalPages = Math.ceil(filteredEvents.length / pageSize) || 1;
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEvents.slice(start, start + pageSize);
  }, [filteredEvents, currentPage, pageSize]);

  return {
    events: paginatedEvents,
    totalEvents: filteredEvents.length,
    searchQuery,
    setSearchQuery,
    severityFilter,
    setSeverityFilter,
    decisionFilter,
    setDecisionFilter,
    currentPage,
    setCurrentPage,
    totalPages,
  };
}
