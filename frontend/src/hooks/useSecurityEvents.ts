/**
 * Custom hook for managing, filtering, searching, and sorting Security Audit Events.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { dashboardApi } from "../services/api";
import type { SecurityEvent } from "../types";

export function useSecurityEvents() {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [decisionFilter, setDecisionFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [backendEvents, setBackendEvents] = useState<SecurityEvent[]>([]);
  const pageSize = 5;

  const fetchEvents = useCallback(async () => {
    try {
      const data = await dashboardApi.getEvents(searchQuery, decisionFilter, severityFilter);
      if (Array.isArray(data)) {
        setBackendEvents(data);
      }
    } catch {
      // API fallback
    }
  }, [searchQuery, decisionFilter, severityFilter]);

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 15000);
    return () => clearInterval(interval);
  }, [fetchEvents]);

  const rawEvents: SecurityEvent[] = useMemo(() => {
    let localEvents: SecurityEvent[] = [];
    try {
      const stored = localStorage.getItem("sentinel_security_events");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          localEvents = parsed;
        }
      }
    } catch {
      // fallback
    }

    // Merge backend and local events without duplicates
    const eventMap = new Map<string, SecurityEvent>();
    backendEvents.forEach((evt) => eventMap.set(evt.id, evt));
    localEvents.forEach((evt) => {
      if (!eventMap.has(evt.id)) {
        eventMap.set(evt.id, evt);
      }
    });

    return Array.from(eventMap.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [backendEvents]);

  const filteredEvents = useMemo(() => {
    return rawEvents.filter((evt) => {
      if (decisionFilter !== "ALL" && evt.decision !== decisionFilter) {
        return false;
      }
      if (severityFilter !== "ALL" && evt.severity !== severityFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inQuestion = (evt.question || "").toLowerCase().includes(q);
        const inReason = (evt.reason || "").toLowerCase().includes(q);
        const inCat = (evt.categories || []).some((c) => c.toLowerCase().includes(q));
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
    refresh: fetchEvents,
  };
}
