import React, { createContext, useContext, useState, useCallback } from "react";
import { chatApi } from "../services/api";
import type { ChatMessage, LeakDetection, SecurityEvent } from "../types";

interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  activeDlpReport: LeakDetection | null;
  error: string | null;
  sendMessage: (questionText: string) => Promise<void>;
  clearChat: () => void;
  setActiveDlpReport: (report: LeakDetection | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeDlpReport, setActiveDlpReport] = useState<LeakDetection | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (questionText: string) => {
    if (!questionText.trim() || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: questionText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.sendQuestion(questionText.trim());

      const assistantMsgId = `assistant-${Date.now()}`;
      const isBlocked = response.leak_detection.decision === "BLOCK";

      const assistantMessage: ChatMessage = {
        id: assistantMsgId,
        sender: "assistant",
        text: isBlocked
          ? "🚫 Response blocked due to enterprise security policy."
          : response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        leakDetection: response.leak_detection,
        sources: response.sources,
        isBlocked: isBlocked,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setActiveDlpReport(response.leak_detection);

      // Save event to local storage for real audit history
      const newEvent: SecurityEvent = {
        id: `evt-${Date.now()}`,
        timestamp: response.leak_detection.timestamp || new Date().toISOString(),
        question: questionText.trim(),
        decision: response.leak_detection.decision,
        severity: response.leak_detection.severity,
        categories: response.leak_detection.categories,
        matchedDocument: response.leak_detection.matched_document || undefined,
        reason: response.leak_detection.reason,
        policyViolation: response.leak_detection.policy_violation,
        confidence: response.leak_detection.confidence,
      };

      try {
        const stored = localStorage.getItem("sentinel_security_events");
        const existingEvents = stored ? JSON.parse(stored) : [];
        localStorage.setItem("sentinel_security_events", JSON.stringify([newEvent, ...existingEvents]));
      } catch {
        // localStorage fallback
      }

    } catch (err: any) {
      const errMsg = err.message || "Failed to communicate with SentinelAI backend.";
      setError(errMsg);

      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: "assistant",
        text: `⚠️ Error: ${errMsg}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setActiveDlpReport(null);
    setError(null);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        activeDlpReport,
        error,
        sendMessage,
        clearChat,
        setActiveDlpReport,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
