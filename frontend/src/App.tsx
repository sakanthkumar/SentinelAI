import React, { useState } from "react";
import { Header } from "./components/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { ChatPage } from "./pages/ChatPage";
import { DocumentCenterPage } from "./pages/DocumentCenterPage";
import { SecurityEventsPage } from "./pages/SecurityEventsPage";
import { DlpPoliciesPage } from "./pages/DlpPoliciesPage";
import { useDashboard } from "./hooks/useDashboard";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const { backendStatus } = useDashboard();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navigation Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
      />

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "dashboard" && (
          <DashboardPage onNavigateToChat={() => setActiveTab("chat")} />
        )}
        {activeTab === "chat" && <ChatPage />}
        {activeTab === "documents" && <DocumentCenterPage />}
        {activeTab === "events" && <SecurityEventsPage />}
        {activeTab === "policies" && <DlpPoliciesPage />}
      </main>
    </div>
  );
}

export default App;
