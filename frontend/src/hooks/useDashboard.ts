/**
 * Custom hook for fetching real Dashboard telemetry from FastAPI backend and local security audit logs.
 */

import { useEffect, useState, useCallback } from "react";
import { dashboardApi, healthApi } from "../services/api";
import type {
  DashboardStats,
  DocumentDetail,
  SecurityEvent,
  SystemHealthResponse,
} from "../types";

const INITIAL_HEALTH: SystemHealthResponse = {
  fastapi: "Healthy",
  chromadb: "Healthy",
  llm: "Healthy",
  policy_engine: "Healthy",
  semantic_dlp: "Healthy",
  overall_status: "Healthy",
};

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    protectedDocuments: 0,
    publicDocuments: 0,
    blockedRequests: 0,
    allowedRequests: 0,
    protectedChunks: 0,
    vaultHealth: "Healthy",
  });

  const [documentsList, setDocumentsList] = useState<DocumentDetail[]>([]);
  const [recentEvents, setRecentEvents] = useState<SecurityEvent[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse>(INITIAL_HEALTH);
  const [backendStatus, setBackendStatus] = useState<"connected" | "connecting" | "offline">("connecting");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchDashboardData = useCallback(async () => {
    // Read actual audit logs from local storage for real Blocked/Allowed metrics & recent activity
    let realEvents: SecurityEvent[] = [];
    try {
      const stored = localStorage.getItem("sentinel_security_events");
      if (stored) {
        realEvents = JSON.parse(stored);
      }
    } catch {
      // fallback
    }

    const realBlocked = realEvents.filter((e) => e.decision === "BLOCK").length;
    const realAllowed = realEvents.filter((e) => e.decision === "ALLOW").length;
    setRecentEvents(realEvents.slice(0, 5));

    try {
      const healthRes = await healthApi.getHealth();
      if (healthRes.status === "running") {
        setBackendStatus("connected");
      }

      const [statsRes, docsRes, healthCompRes] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getDocuments(),
        dashboardApi.getSystemHealth(),
      ]);

      setStats({
        totalDocuments: statsRes.total_documents,
        protectedDocuments: statsRes.protected_documents,
        publicDocuments: statsRes.public_documents,
        blockedRequests: realBlocked,
        allowedRequests: realAllowed,
        protectedChunks: statsRes.protected_chunks,
        vaultHealth: statsRes.vault_health,
      });

      setDocumentsList(docsRes);
      setSystemHealth(healthCompRes);
    } catch {
      setBackendStatus("offline");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  return {
    stats,
    documentsList,
    recentEvents,
    systemHealth,
    backendStatus,
    isLoading,
    refresh: fetchDashboardData,
  };
}
