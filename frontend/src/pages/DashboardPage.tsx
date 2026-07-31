import React, { memo } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  FileText,
  Lock,
  CheckCircle2,
  AlertCircle,
  Database,
  ArrowUpRight,
  RefreshCw,
  Server,
  Globe,
  Clock,
  Inbox,
} from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import type { DocumentDetail, SecurityEvent } from "../types";

const DocumentRow = memo(({ doc }: { doc: DocumentDetail }) => {
  const isConfidential = doc.classification.toLowerCase() === "confidential";
  return (
    <tr className="hover:bg-slate-800/40 transition-colors">
      <td className="py-3 px-3 font-semibold text-slate-200 flex items-center gap-2">
        <FileText className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
        <span className="truncate max-w-[160px]">{doc.name}</span>
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${
            isConfidential
              ? "bg-purple-950 text-purple-300 border border-purple-800/60"
              : "bg-cyan-950 text-cyan-300 border border-cyan-800/60"
          }`}
        >
          {isConfidential ? (
            <Lock className="w-2.5 h-2.5" aria-hidden="true" />
          ) : (
            <Globe className="w-2.5 h-2.5" aria-hidden="true" />
          )}
          <span>{doc.classification}</span>
        </span>
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        {doc.indexed ? (
          <span className="text-emerald-400 font-semibold text-[11px] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Indexed
          </span>
        ) : (
          <span className="text-slate-500 text-[11px]">Pending</span>
        )}
      </td>
      <td className="py-3 px-3 font-mono text-[11px] text-slate-300 whitespace-nowrap">
        {isConfidential ? "Protected Vault" : "Public Repository"}
      </td>
    </tr>
  );
});
DocumentRow.displayName = "DocumentRow";

const ActivityRow = memo(({ evt }: { evt: SecurityEvent }) => {
  const isBlock = evt?.decision === "BLOCK";
  const categoriesList = Array.isArray(evt?.categories) ? evt.categories : [];
  const displayTime = evt?.timestamp ? new Date(evt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "--:--";
  return (
    <tr className="hover:bg-slate-800/40 transition-colors">
      <td className="py-3 px-3 font-mono text-slate-400 text-[11px] whitespace-nowrap">
        {displayTime}
      </td>
      <td className="py-3 px-3 font-medium text-slate-200 max-w-[140px] truncate">
        {evt?.question || "N/A"}
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        {isBlock ? (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800/80">
            POLICY VIOLATION
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800/80">
            COMPLIANT
          </span>
        )}
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
          {evt?.severity || "LOW"}
        </span>
      </td>
      <td className="py-3 px-3 font-mono text-[10px] text-indigo-300 whitespace-nowrap">
        {categoriesList[0] || "GENERAL"}
      </td>
    </tr>
  );
});
ActivityRow.displayName = "ActivityRow";

export const DashboardPage: React.FC<{ onNavigateToChat: () => void }> = ({ onNavigateToChat }) => {
  const {
    stats,
    documentsList,
    recentEvents,
    systemHealth,
    backendStatus,
    isLoading,
    refresh,
  } = useDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse" aria-label="Loading Dashboard Data">
        <div className="h-24 bg-slate-900 border border-slate-800 rounded-2xl"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-900 border border-slate-800 rounded-2xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl"></div>
          <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Semantic DLP Security Overview
            {backendStatus === "connected" ? (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true"></span>
                Backend Live
              </span>
            ) : (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-950 text-rose-400 border border-rose-800/60 font-semibold flex items-center gap-1">
                <AlertCircle className="w-3 h-3" aria-hidden="true" />
                Backend Offline - Reconnecting...
              </span>
            )}
          </h1>
          <p className="text-slate-400 text-sm">
            Real-time RAG query monitoring, confidential reference vault state, and enterprise data loss prevention.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            aria-label="Refresh backend telemetry"
            title="Refresh backend telemetry"
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
          </button>
          <button
            onClick={onNavigateToChat}
            aria-label="Navigate to Test Prompt Security Chat"
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-indigo-500/25 transition-all duration-200 flex items-center justify-center gap-2 self-start md:self-auto focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <span>Test Prompt Security</span>
            <ArrowUpRight className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* 4 Cards: Total Documents, Protected Vault, Enterprise Policy Violations, Policy Compliant Queries */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Knowledge Documents */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Knowledge Documents</span>
            <div className="p-2 rounded-xl bg-cyan-950/60 text-cyan-400 border border-cyan-800/40">
              <FileText className="w-5 h-5" aria-hidden="true" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white tracking-tight">{stats.totalDocuments}</span>
            <span className="text-xs font-medium text-slate-400">Knowledge Base</span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800/80 pt-2.5">
            <span className="text-cyan-400 font-semibold">{stats.publicDocuments} Public</span>
            <span>•</span>
            <span className="text-purple-400 font-semibold">{stats.protectedDocuments} Confidential</span>
          </div>
        </div>

        {/* Card 2: Protected Reference Vault */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Protected Reference Vault</span>
            <div className="p-2 rounded-xl bg-purple-950/60 text-purple-400 border border-purple-800/40">
              <Lock className="w-5 h-5" aria-hidden="true" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white tracking-tight">{stats.protectedDocuments}</span>
            <span className="text-xs font-medium text-purple-400 font-semibold">protected_vault</span>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400 border-t border-slate-800/80 pt-2.5">
            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{stats.protectedChunks} Vector Chunks Stored</span>
          </div>
        </div>

        {/* Card 3: Enterprise Policy Violations */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Enterprise Policy Violations</span>
            <div className="p-2 rounded-xl bg-rose-950/60 text-rose-400 border border-rose-800/40">
              <ShieldAlert className="w-5 h-5" aria-hidden="true" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-rose-400 tracking-tight">{stats.blockedRequests}</span>
            <span className="text-xs font-medium text-slate-400">Exfiltrations Blocked</span>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-rose-400/90 border-t border-slate-800/80 pt-2.5 font-medium">
            <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Secrets Redacted</span>
          </div>
        </div>

        {/* Card 4: Policy Compliant Queries */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Policy Compliant Queries</span>
            <div className="p-2 rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
              <ShieldCheck className="w-5 h-5" aria-hidden="true" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-emerald-400 tracking-tight">{stats.allowedRequests}</span>
            <span className="text-xs font-medium text-slate-400">Allowed Responses</span>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-400 border-t border-slate-800/80 pt-2.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
            <span>Sanitized Sources</span>
          </div>
        </div>
      </div>

      {/* Two Columns: Recent Security Activity (Left) & Protected Documents (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Table 1: Recent Security Activity */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" aria-hidden="true" />
              Recent Security Activity
            </h2>
            <span className="text-[11px] text-slate-400">Live Audit Telemetry</span>
          </div>

          {recentEvents.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs" aria-label="Recent Security Activity Table">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                    <th className="py-2.5 px-3">Time</th>
                    <th className="py-2.5 px-3">Question</th>
                    <th className="py-2.5 px-3">Decision</th>
                    <th className="py-2.5 px-3">Severity</th>
                    <th className="py-2.5 px-3">Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {recentEvents.map((evt) => (
                    <ActivityRow key={evt.id} evt={evt} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
              <Inbox className="w-8 h-8 text-slate-600" aria-hidden="true" />
              <p className="text-xs font-semibold text-slate-400">No Security Activity Recorded</p>
              <p className="text-[11px] text-slate-500 max-w-xs">
                Submit prompt queries in Secure Chat to generate real security telemetry.
              </p>
            </div>
          )}
        </div>

        {/* Table 2: Protected Documents */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" aria-hidden="true" />
              Protected Knowledge Repository
            </h2>
            <span className="text-[11px] text-slate-400">Vector Storage</span>
          </div>

          {documentsList.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs" aria-label="Protected Knowledge Repository Table">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                    <th className="py-2.5 px-3">Document Name</th>
                    <th className="py-2.5 px-3">Classification</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Repository</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {documentsList.map((doc, idx) => (
                    <DocumentRow key={idx} doc={doc} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
              <FileText className="w-8 h-8 text-slate-600" aria-hidden="true" />
              <p className="text-xs font-semibold text-slate-400">No Documents Ingested</p>
              <p className="text-[11px] text-slate-500 max-w-xs">
                Upload files or trigger bulk ingestion in Document Center.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Compact System Components Health Panel */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-cyan-400" aria-hidden="true" />
            <h2 className="text-sm font-bold text-white">System Components Health</h2>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono font-semibold">
            {systemHealth.overall_status}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">✓ FastAPI</span>
            <span className={`font-bold flex items-center gap-1 ${systemHealth.fastapi === "Healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              <span className={`w-2 h-2 rounded-full ${systemHealth.fastapi === "Healthy" ? "bg-emerald-400" : "bg-rose-400"}`} aria-hidden="true"></span>
              {systemHealth.fastapi}
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">✓ ChromaDB</span>
            <span className={`font-bold flex items-center gap-1 ${systemHealth.chromadb === "Healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              <span className={`w-2 h-2 rounded-full ${systemHealth.chromadb === "Healthy" ? "bg-emerald-400" : "bg-rose-400"}`} aria-hidden="true"></span>
              {systemHealth.chromadb}
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">✓ Ollama / LLM</span>
            <span className={`font-bold flex items-center gap-1 ${systemHealth.llm === "Healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              <span className={`w-2 h-2 rounded-full ${systemHealth.llm === "Healthy" ? "bg-emerald-400" : "bg-rose-400"}`} aria-hidden="true"></span>
              {systemHealth.llm}
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">✓ Semantic DLP</span>
            <span className={`font-bold flex items-center gap-1 ${systemHealth.semantic_dlp === "Healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              <span className={`w-2 h-2 rounded-full ${systemHealth.semantic_dlp === "Healthy" ? "bg-emerald-400" : "bg-rose-400"}`} aria-hidden="true"></span>
              {systemHealth.semantic_dlp}
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">✓ Policy Engine</span>
            <span className={`font-bold flex items-center gap-1 ${systemHealth.policy_engine === "Healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              <span className={`w-2 h-2 rounded-full ${systemHealth.policy_engine === "Healthy" ? "bg-emerald-400" : "bg-rose-400"}`} aria-hidden="true"></span>
              {systemHealth.policy_engine}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
