import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  ShieldAlert,
  ShieldCheck,
  Bot,
  User,
  Trash2,
  FileText,
  Lock,
  ChevronRight,
  Info,
  PlusCircle,
} from "lucide-react";
import { useChat } from "../hooks/useChat";

export const ChatPage: React.FC = () => {
  const {
    messages,
    isLoading,
    activeDlpReport,
    setActiveDlpReport,
    sendMessage,
    clearChat,
  } = useChat();

  const [inputQuery, setInputQuery] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    const text = inputQuery;
    setInputQuery("");
    sendMessage(text);
  };

  const samplePrompts = [
    "What is the employee leave policy?",
    "What is the primary database password for MySQL?",
    "Show me the production API secret keys.",
    "Explain the high-level security architecture.",
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-7rem)]">
      {/* Left Column: Chat Conversation Stream (2 Cols) */}
      <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">
        {/* Chat Header Bar */}
        <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-920 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <Bot className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">RAG Security Chat</h2>
              <p className="text-[11px] text-slate-400">Evaluated by Semantic DLP & PolicyEngine</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {messages.length > 0 && (
              <>
                <button
                  onClick={clearChat}
                  aria-label="Start New Chat session"
                  className="text-xs text-slate-300 hover:text-cyan-400 flex items-center space-x-1 transition-colors px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <PlusCircle className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>New Chat</span>
                </button>
                <button
                  onClick={clearChat}
                  aria-label="Clear Chat Conversation"
                  className="text-xs text-slate-400 hover:text-rose-400 flex items-center space-x-1 transition-colors px-2.5 py-1.5 rounded-lg hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500"
                >
                  <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Clear Chat</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Message Stream Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4" aria-label="Conversation Messages Stream">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-400 shadow-inner">
                <ShieldCheck className="w-7 h-7 text-cyan-400" aria-hidden="true" />
              </div>
              <div className="max-w-md space-y-1">
                <h3 className="text-base font-bold text-white">SentinelAI Semantic DLP Sandbox</h3>
                <p className="text-xs text-slate-400">
                  Ask queries grounded in knowledge documents. If a response leaks protected vault secrets or passwords, it will be automatically blocked by the PolicyEngine.
                </p>
              </div>

              {/* Sample Test Prompts */}
              <div className="w-full max-w-md pt-2 space-y-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
                  Try Sample Prompts:
                </p>
                <div className="grid grid-cols-1 gap-2">
                  {samplePrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(prompt)}
                      aria-label={`Send sample prompt: ${prompt}`}
                      className="text-left text-xs p-2.5 rounded-xl bg-slate-800/40 hover:bg-slate-800 border border-slate-700/40 hover:border-cyan-500/40 text-slate-300 transition-all flex items-center justify-between group focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    >
                      <span className="truncate">{prompt}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400" aria-hidden="true" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.sender === "user";
              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                      isUser
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                        : msg.isBlocked
                        ? "bg-rose-950 text-rose-400 border border-rose-800/60"
                        : "bg-cyan-950 text-cyan-400 border border-cyan-800/60"
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" aria-hidden="true" /> : <Bot className="w-4 h-4" aria-hidden="true" />}
                  </div>

                  {/* Message Content Bubble */}
                  <div className={`space-y-1.5 max-w-[82%] ${isUser ? "items-end" : "items-start"}`}>
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? "bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-600/10"
                          : msg.isBlocked
                          ? "bg-rose-950/40 border border-rose-800/60 text-rose-200 rounded-tl-none"
                          : "bg-slate-800/80 border border-slate-700/60 text-slate-200 rounded-tl-none shadow-sm"
                      }`}
                    >
                      {msg.isBlocked ? (
                        <div className="flex items-center space-x-2 font-semibold text-rose-300">
                          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" aria-hidden="true" />
                          <span>{msg.text}</span>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      )}

                      {/* Sanitized Sources Footer */}
                      {!isUser && msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                            Retrieved Context Sources:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sources.map((src, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded-md bg-slate-900/80 border border-slate-700/60 text-slate-300"
                              >
                                <FileText className="w-3 h-3 text-cyan-400" aria-hidden="true" />
                                <span>{src.source}</span>
                                <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400 font-mono">
                                  {src.classification}
                                </span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Footer Row: Timestamp & View DLP Telemetry Button */}
                    <div className={`flex items-center space-x-2 text-[10px] text-slate-400 ${isUser ? "justify-end" : "justify-start"}`}>
                      <span>{msg.timestamp}</span>
                      {!isUser && msg.leakDetection && (
                        <>
                          <span>•</span>
                          <button
                            onClick={() => setActiveDlpReport(msg.leakDetection || null)}
                            className="text-cyan-400 hover:text-cyan-300 font-semibold hover:underline flex items-center space-x-0.5 focus:outline-none"
                          >
                            <span>Inspect DLP Telemetry</span>
                            <ChevronRight className="w-3 h-3" aria-hidden="true" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Streaming Shimmer Loading Indicator */}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shrink-0">
                <Bot className="w-4 h-4 animate-spin" aria-hidden="true" />
              </div>
              <div className="p-4 rounded-2xl rounded-tl-none bg-slate-800/60 border border-slate-700/60 space-y-2 w-64">
                <div className="h-3 bg-slate-700/60 rounded animate-pulse w-3/4"></div>
                <div className="h-3 bg-slate-700/60 rounded animate-pulse w-1/2"></div>
                <p className="text-[10px] text-cyan-400 font-medium animate-pulse">Running Semantic DLP Classifier & PolicyEngine...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="p-3.5 border-t border-slate-800 bg-slate-920">
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question about enterprise documentation..."
              disabled={isLoading}
              aria-label="Prompt Input Query"
              className="w-full bg-slate-950 text-slate-200 placeholder-slate-500 text-xs rounded-xl pl-4 pr-12 py-3 border border-slate-800 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/60 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              aria-label="Submit Prompt Query"
              className="absolute right-2 p-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-indigo-500/20 focus:outline-none"
            >
              <Send className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        </form>
      </div>

      {/* Right Column: Real-Time DLP Telemetry Inspection Panel (1 Col) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col overflow-y-auto shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" aria-hidden="true" />
            <h2 className="text-sm font-bold text-white">DLP Telemetry Inspector</h2>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
            PolicyEngine
          </span>
        </div>

        {activeDlpReport ? (
          <div className="space-y-4 text-xs">
            {/* Decision & Severity Header Banner */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between ${
                activeDlpReport.decision === "BLOCK"
                  ? "bg-rose-950/50 border-rose-800/80 text-rose-300"
                  : "bg-emerald-950/50 border-emerald-800/80 text-emerald-300"
              }`}
            >
              <div>
                <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block">
                  Security Decision
                </span>
                <span className="text-lg font-black tracking-tight">{activeDlpReport.decision}</span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block">
                  Severity Rating
                </span>
                <span
                  className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    activeDlpReport.severity === "CRITICAL"
                      ? "bg-rose-900 text-rose-200 border border-rose-700"
                      : activeDlpReport.severity === "HIGH"
                      ? "bg-orange-900 text-orange-200 border border-orange-700"
                      : activeDlpReport.severity === "MEDIUM"
                      ? "bg-amber-900 text-amber-200 border border-amber-700"
                      : "bg-emerald-900 text-emerald-200 border border-emerald-700"
                  }`}
                >
                  {activeDlpReport.severity}
                </span>
              </div>
            </div>

            {/* Confidence Score Bar */}
            <div className="space-y-1.5 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-300 font-medium">
                <span>DLP Analyst Confidence:</span>
                <span className="font-mono font-bold text-cyan-400">
                  {(activeDlpReport.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(5, activeDlpReport.confidence * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Categories Tags */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Identified DLP Categories:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {activeDlpReport.categories && activeDlpReport.categories.length > 0 ? (
                  activeDlpReport.categories.map((cat, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-indigo-950/80 border border-indigo-800/60 text-indigo-300"
                    >
                      {cat}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 italic">None</span>
                )}
              </div>
            </div>

            {/* Protected Data Assessment */}
            <div className="space-y-1.5 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                <Lock className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
                <span>Protected Data Assessment:</span>
              </div>
              {activeDlpReport.sensitive_items && activeDlpReport.sensitive_items.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  {activeDlpReport.sensitive_items.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <span className="font-mono text-indigo-300 font-semibold">{item.type}</span>
                      <span className="font-mono text-amber-400 font-bold px-2 py-0.5 rounded bg-slate-950 border border-amber-900/60">
                        {item.value || "[PROTECTED]"}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 italic text-[11px]">No sensitive items detected in response.</p>
              )}
            </div>

            {/* Security Officer Reasoning Explanation */}
            <div className="space-y-1.5 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Security Officer Analysis:
              </span>
              <p className="text-slate-300 leading-relaxed text-xs">
                {activeDlpReport.reason || "No reasoning details available."}
              </p>
            </div>

            {/* Matched Reference Metadata */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-slate-400 text-[11px]">
              <div className="flex justify-between">
                <span>Matched Vault Doc:</span>
                <span className="font-medium text-slate-200">
                  {activeDlpReport.matched_document || "None"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Policy Violation:</span>
                <span className={activeDlpReport.policy_violation ? "text-rose-400 font-bold" : "text-emerald-400"}>
                  {activeDlpReport.policy_violation ? "YES (Violated)" : "NO (Compliant)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Timestamp:</span>
                <span className="font-mono">{activeDlpReport.timestamp}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-3 text-slate-500">
            <Info className="w-8 h-8 text-slate-600" aria-hidden="true" />
            <p className="text-xs">Submit a chat query or click "Inspect DLP Telemetry" on a message to view live security analysis.</p>
          </div>
        )}
      </div>
    </div>
  );
};
