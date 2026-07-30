import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  Lock,
  Inbox,
} from "lucide-react";
import { useSecurityEvents } from "../hooks/useSecurityEvents";

export const SecurityEventsPage: React.FC = () => {
  const {
    events,
    totalEvents,
    searchQuery,
    setSearchQuery,
    severityFilter,
    setSeverityFilter,
    decisionFilter,
    setDecisionFilter,
    currentPage,
    setCurrentPage,
    totalPages,
  } = useSecurityEvents();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Security Audit Log & DLP Events
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800/60 font-semibold">
              SIEM Ready
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Auditable records of exfiltration prevention decisions, category violations, and policy enforcement telemetry.
          </p>
        </div>
        <div className="text-xs text-slate-400 font-mono bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 self-start md:self-auto">
          Total Recorded Events: <span className="text-cyan-400 font-bold">{totalEvents}</span>
        </div>
      </div>

      {/* Control Toolbar: Search & Filters */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search Bar */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search prompts, reasons, or categories..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            aria-label="Search audit events"
            className="w-full bg-slate-950 text-slate-200 text-xs rounded-xl pl-9 pr-3 py-2.5 border border-slate-800 focus:outline-none focus:border-cyan-500/60"
          />
        </div>

        {/* Filters Row */}
        <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
          <div className="flex items-center space-x-2 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <label htmlFor="decision-filter" className="text-slate-400 font-medium">Decision:</label>
            <select
              id="decision-filter"
              value={decisionFilter}
              onChange={(e) => {
                setDecisionFilter(e.target.value);
                setCurrentPage(1);
              }}
              aria-label="Filter events by decision"
              className="bg-slate-950 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 border border-slate-800 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Decisions</option>
              <option value="BLOCK">POLICY VIOLATIONS Only</option>
              <option value="ALLOW">COMPLIANT Only</option>
            </select>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <label htmlFor="severity-filter" className="text-slate-400 font-medium">Severity:</label>
            <select
              id="severity-filter"
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setCurrentPage(1);
              }}
              aria-label="Filter events by severity"
              className="bg-slate-950 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 border border-slate-800 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {events.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" aria-label="Security Audit Logs Table">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Prompt Query</th>
                  <th className="py-3 px-4">DLP Categories</th>
                  <th className="py-3 px-4">Analysis & Policy Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {evt.decision === "BLOCK" ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold bg-rose-950 text-rose-300 border border-rose-800/80">
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />
                          <span>POLICY VIOLATION</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800/80">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
                          <span>COMPLIANT</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          evt.severity === "CRITICAL"
                            ? "bg-rose-900 text-rose-200"
                            : evt.severity === "HIGH"
                            ? "bg-orange-900 text-orange-200"
                            : evt.severity === "MEDIUM"
                            ? "bg-amber-900 text-amber-200"
                            : "bg-emerald-900 text-emerald-200"
                        }`}
                      >
                        {evt.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200 max-w-xs truncate">
                      {evt.question}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1">
                        {evt.categories.map((cat, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800/60"
                          >
                            {cat}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 max-w-md text-[11px] leading-relaxed">
                      <div className="flex items-start gap-1.5">
                        {evt.policyViolation && <Lock className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" aria-hidden="true" />}
                        <span>{evt.reason}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 flex flex-col items-center justify-center text-center space-y-3 text-slate-500 bg-slate-950/40">
            <Inbox className="w-10 h-10 text-slate-600" aria-hidden="true" />
            <p className="text-sm font-semibold text-slate-400">No Security Events Match Filter Criteria</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Try resetting your search query or decision/severity filter settings.
            </p>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            Showing Page <span className="font-semibold text-slate-200">{currentPage}</span> of{" "}
            <span className="font-semibold text-slate-200">{totalPages}</span>
          </span>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous Page"
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next Page"
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
