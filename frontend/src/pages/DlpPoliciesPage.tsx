import React from "react";
import { Lock, Sliders, Ban, Code } from "lucide-react";

export const DlpPoliciesPage: React.FC = () => {
  const blockedCategories = [
    "PASSWORD",
    "DATABASE_CREDENTIAL",
    "API_KEY",
    "TOKEN",
    "SECRET",
    "SSH_KEY",
    "PRIVATE_KEY",
    "CONNECTION_STRING",
    "INTERNAL_HOSTNAME",
    "INTERNAL_IP",
    "CUSTOMER_PII",
    "EMPLOYEE_PII",
    "FINANCIAL_DATA",
    "TRADE_SECRET",
    "PROPRIETARY_ALGORITHM",
    "BUSINESS_PLAN",
  ];

  const allowedCategories = ["GENERAL_INFORMATION", "SECURITY_POLICY", "OTHER"];

  const sensitivityLevels = [
    { level: "PUBLIC", strictness: "LOW", policy: "ALLOW", desc: "Publicly accessible documentation." },
    { level: "INTERNAL", strictness: "MEDIUM", policy: "ALLOW", desc: "Internal company policies and generic procedures." },
    { level: "CONFIDENTIAL", strictness: "HIGH", policy: "EVALUATE", desc: "Confidential company assets, architecture, and financial metrics." },
    { level: "RESTRICTED", strictness: "HIGH", policy: "EVALUATE", desc: "Restricted data containing PII or proprietary IP." },
    { level: "SECRET", strictness: "CRITICAL", policy: "BLOCK", desc: "Strict secrets, cleartext credentials, keys, and infrastructure." },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Enterprise DLP Policy Engine Configuration
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
              PolicyEngine v2.0
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Declarative security policy enforcement rules, category blocking definitions, and document sensitivity controls.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-300 font-mono bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 self-start md:self-auto">
          <Sliders className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
          <span>Config Path: SentinelAI/backend/config/dlp_policy.yaml</span>
        </div>
      </div>

      {/* Two Columns: Category Rules (Left) & Sensitivity Levels (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Blocked vs Allowed Categories Card */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Ban className="w-4 h-4 text-rose-400" aria-hidden="true" />
            Category Blocking & Enforcement Rules
          </h2>

          {/* Blocked Categories */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-rose-300 flex items-center gap-1.5 uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-rose-500" aria-hidden="true"></span>
              Blocked Categories (Exfiltrations Automatically Blocked):
            </span>
            <div className="flex flex-wrap gap-1.5 bg-slate-950 p-3 rounded-xl border border-slate-800">
              {blockedCategories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-rose-950/80 border border-rose-800/60 text-rose-300"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          {/* Allowed Categories */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-emerald-300 flex items-center gap-1.5 uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-emerald-500" aria-hidden="true"></span>
              Allowed Categories (Approved General Knowledge):
            </span>
            <div className="flex flex-wrap gap-1.5 bg-slate-950 p-3 rounded-xl border border-slate-800">
              {allowedCategories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-emerald-950/80 border border-emerald-800/60 text-emerald-300"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Document Sensitivity Matrix */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-purple-400" aria-hidden="true" />
            Document Sensitivity Level Controls
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs" aria-label="Document Sensitivity Matrix Table">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                  <th className="py-2.5 px-3">Sensitivity</th>
                  <th className="py-2.5 px-3">Strictness</th>
                  <th className="py-2.5 px-3">Default Action</th>
                  <th className="py-2.5 px-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {sensitivityLevels.map((lvl) => (
                  <tr key={lvl.level} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3 font-mono font-bold text-slate-200">{lvl.level}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          lvl.strictness === "CRITICAL"
                            ? "bg-rose-950 text-rose-300"
                            : lvl.strictness === "HIGH"
                            ? "bg-purple-950 text-purple-300"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {lvl.strictness}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-slate-300">{lvl.policy}</td>
                    <td className="py-3 px-3 text-slate-400 text-[11px]">{lvl.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Code YAML Configuration Preview */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Code className="w-4 h-4 text-cyan-400" aria-hidden="true" />
            Declarative Policy YAML Config Preview
          </h3>
          <span className="text-xs text-slate-400 font-mono">dlp_policy.yaml</span>
        </div>

        <pre className="bg-slate-950 p-4 rounded-xl text-xs font-mono text-cyan-300 border border-slate-800 overflow-x-auto">
{`policy_name: "Enterprise Data Loss Prevention Policy"
version: "2.0.0"
confidence_threshold: 0.80
default_replacement_message: "Response blocked due to enterprise security policy."

blocked_categories:
  - PASSWORD
  - DATABASE_CREDENTIAL
  - API_KEY
  - TOKEN
  - SECRET
  - SSH_KEY
  - PRIVATE_KEY
  - CONNECTION_STRING
  - INTERNAL_HOSTNAME
  - INTERNAL_IP
  - CUSTOMER_PII
  - EMPLOYEE_PII
  - FINANCIAL_DATA
  - TRADE_SECRET
  - PROPRIETARY_ALGORITHM
  - BUSINESS_PLAN`}
        </pre>
      </div>
    </div>
  );
};
