/**
 * SentinelAI API Client Layer connecting React frontend to FastAPI backend.
 */

import type {
  BulkIngestResponse,
  ChatRequest,
  ChatResponse,
  DashboardStatsResponse,
  DocumentDetail,
  HealthResponse,
  SystemHealthResponse,
  UploadResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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
  async upload(file: File, classification: string = "public"): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("classification", classification);

    const response = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<UploadResponse>(response);
  },

  async bulkIngest(): Promise<BulkIngestResponse> {
    const response = await fetch(`${BASE_URL}/api/knowledge-base/ingest`, {
      method: "POST",
    });
    return handleResponse<BulkIngestResponse>(response);
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
};

export const healthApi = {
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${BASE_URL}/health`, {
      method: "GET",
    });
    return handleResponse<HealthResponse>(response);
  },
};
