import React from "react";
import { ShieldCheck, Server, AlertTriangle } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  backendStatus: "connected" | "connecting" | "offline";
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, backendStatus }) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "chat", label: "Secure Chat" },
    { id: "documents", label: "Document Center" },
    { id: "events", label: "Security Events" },
    { id: "policies", label: "DLP Policies" },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & System Name */}
          <div
            className="flex items-center space-x-3 cursor-pointer focus:outline-none"
            onClick={() => setActiveTab("dashboard")}
            role="button"
            tabIndex={0}
            aria-label="SentinelAI Dashboard Home"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                setActiveTab("dashboard");
              }
            }}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-cyan-400" aria-hidden="true" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  SentinelAI
                </span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                  Semantic DLP
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Enterprise Data Loss Prevention Platform</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1" aria-label="Main Navigation">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  aria-label={`Navigate to ${tab.label}`}
                  aria-current={isActive ? "page" : undefined}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-cyan-500 ${
                    isActive
                      ? "bg-slate-800 text-white shadow-sm border border-slate-700/60"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Backend Status Telemetry Pill */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-850 border border-slate-800 text-xs">
              <Server className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              <span className="text-slate-300 font-medium">FastAPI Engine:</span>
              {backendStatus === "connected" && (
                <span className="flex items-center text-emerald-400 font-semibold space-x-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true"></span>
                  <span>Active</span>
                </span>
              )}
              {backendStatus === "connecting" && (
                <span className="flex items-center text-amber-400 font-semibold space-x-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" aria-hidden="true"></span>
                  <span>Checking</span>
                </span>
              )}
              {backendStatus === "offline" && (
                <span className="flex items-center text-rose-400 font-semibold space-x-1">
                  <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                  <span>Offline</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="flex md:hidden overflow-x-auto space-x-1 py-2 border-t border-slate-800/80" aria-label="Mobile Navigation">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                aria-label={`Navigate to ${tab.label}`}
                className={`px-3 py-1.5 text-xs font-medium whitespace-nowrap rounded-md ${
                  isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
