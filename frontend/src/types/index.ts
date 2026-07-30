/**
 * SentinelAI Enterprise Semantic DLP Platform TypeScript Type Definitions.
 */

export interface SensitiveItem {
  type: string;
  value: string;
  redacted?: boolean;
}

export interface LeakDetection {
  decision: "ALLOW" | "BLOCK";
  blocked: boolean;
  similarity: number;
  risk: string;
  overlap: boolean;
  confidence: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  categories: string[];
  sensitive_items: SensitiveItem[];
  reason: string;
  policy_violation: boolean;
  timestamp: string;
  matched_document?: string | null;
  metadata?: Record<string, any>;
  replacement_response?: string | null;
}

export interface SanitizedSource {
  source: string;
  classification: string;
  document_type: string;
  content?: string;
}

export interface ChatRequest {
  question: string;
  top_k?: number;
}

export interface ChatResponse {
  question: string;
  answer: string;
  sources: SanitizedSource[];
  retrieved_documents: number;
  leak_detection: LeakDetection;
}

export interface UploadResponse {
  status: string;
  filename: string;
  classification: string;
  chunks: number;
  collection: string;
}

export interface FailureDetail {
  file: string;
  reason: string;
}

export interface BulkIngestResponse {
  status: string;
  documents_processed: number;
  public_documents: number;
  confidential_documents: number;
  total_chunks: number;
  failed_documents: number;
  failures: FailureDetail[];
  processing_time_seconds: number;
}

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
}

export interface DocumentDetail {
  name: string;
  classification: string;
  indexed: boolean;
  source: string;
  chunks: number;
}

export interface DashboardStatsResponse {
  total_documents: number;
  public_documents: number;
  confidential_documents: number;
  protected_documents: number;
  protected_chunks: number;
  vault_health: string;
  blocked_requests: number;
  allowed_requests: number;
}

export interface SystemHealthResponse {
  fastapi: string;
  chromadb: string;
  llm: string;
  policy_engine: string;
  semantic_dlp: string;
  overall_status: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  leakDetection?: LeakDetection;
  sources?: SanitizedSource[];
  isBlocked?: boolean;
}

export interface SecurityEvent {
  id: string;
  timestamp: string;
  question: string;
  decision: "ALLOW" | "BLOCK";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  categories: string[];
  matchedDocument?: string;
  reason: string;
  policyViolation: boolean;
  confidence: number;
}

export interface DocumentItem {
  id: string;
  name: string;
  classification: "public" | "confidential";
  documentType: string;
  chunks: number;
  status: "indexed" | "protected" | "uploading" | "failed";
  uploadedAt: string;
}

export interface DashboardStats {
  totalDocuments: number;
  protectedDocuments: number;
  publicDocuments: number;
  blockedRequests: number;
  allowedRequests: number;
  protectedChunks: number;
  vaultHealth: string;
}
