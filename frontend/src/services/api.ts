/**
 * SentinelAI API Client Layer connecting React frontend to FastAPI backend.
 */

import type {
  ChatRequest,
  ChatResponse,
  DashboardStatsResponse,
  DocumentDetail,
  HealthResponse,
  SystemHealthResponse,
  UploadResponse,
} from "../types";

const getBaseUrl = (): string => {
  const rawUrl = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").trim();
  return rawUrl.replace(/\/+$/, "").replace(/\/health$/, "");
};

const BASE_URL = getBaseUrl();

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API Request failed with status ${response.status}`;
    let errorDetails = null;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorMessage = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
      errorDetails = errorJson;
    } catch {
      // Non-JSON response
    }
    throw new ApiError(response.status, errorMessage, errorDetails);
  }
  return response.json();
}

export const chatApi = {
  async sendQuestion(question: string, top_k: number = 5): Promise<ChatResponse> {
    const payload: ChatRequest = { question, top_k };
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<ChatResponse>(response);
  },
};

export const documentsApi = {
  async upload(files: File | File[], classification: string = "public"): Promise<any> {
    const formData = new FormData();
    const fileArray = Array.isArray(files) ? files : [files];
    fileArray.forEach((file) => formData.append("files", file));
    formData.append("classification", classification);

    const response = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<any>(response);
  },

  async list(): Promise<DocumentDetail[]> {
    const response = await fetch(`${BASE_URL}/api/documents`, {
      method: "GET",
    });
    return handleResponse<DocumentDetail[]>(response);
  },

  async deleteDocument(documentId: string): Promise<any> {
    const response = await fetch(`${BASE_URL}/api/documents/${encodeURIComponent(documentId)}`, {
      method: "DELETE",
    });
    return handleResponse<any>(response);
  },
};

export const dashboardApi = {
  async getStats(): Promise<DashboardStatsResponse> {
    const response = await fetch(`${BASE_URL}/api/dashboard/stats`, {
      method: "GET",
    });
    return handleResponse<DashboardStatsResponse>(response);
  },

  async getDocuments(): Promise<DocumentDetail[]> {
    const response = await fetch(`${BASE_URL}/api/dashboard/documents`, {
      method: "GET",
    });
    return handleResponse<DocumentDetail[]>(response);
  },

  async getSystemHealth(): Promise<SystemHealthResponse> {
    const response = await fetch(`${BASE_URL}/api/dashboard/system-health`, {
      method: "GET",
    });
    return handleResponse<SystemHealthResponse>(response);
  },

  async getEvents(search?: string, decision?: string, severity?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (decision && decision !== "ALL") params.append("decision", decision);
    if (severity && severity !== "ALL") params.append("severity", severity);
    const queryString = params.toString() ? `?${params.toString()}` : "";

    const response = await fetch(`${BASE_URL}/api/dashboard/events${queryString}`, {
      method: "GET",
    });
    return handleResponse<any[]>(response);
  },
};

export const healthApi = {
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${BASE_URL}/health`, {
      method: "GET",
    });
    return handleResponse<HealthResponse>(response);
  },
};
