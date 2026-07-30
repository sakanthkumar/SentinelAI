/**
 * Custom hook for managing document upload queue and bulk ingestion.
 */

import { useCallback, useState } from "react";
import { documentsApi } from "../services/api";
import type { BulkIngestResponse, DocumentItem, UploadResponse } from "../types";

export function useUpload() {
  const [documents, setDocuments] = useState<DocumentItem[]>(() => {
    try {
      const stored = localStorage.getItem("sentinel_documents");
      if (stored) return JSON.parse(stored);
    } catch {
      // fallback
    }
    return [
      {
        id: "doc-1",
        name: "company_faq.pdf",
        classification: "public",
        documentType: "policy",
        chunks: 14,
        status: "indexed",
        uploadedAt: "2026-07-30 10:00",
      },
      {
        id: "doc-2",
        name: "financial_report_q2_2026.pdf",
        classification: "confidential",
        documentType: "financial",
        chunks: 32,
        status: "protected",
        uploadedAt: "2026-07-30 10:15",
      },
      {
        id: "doc-3",
        name: "database_credentials.pdf",
        classification: "confidential",
        documentType: "database",
        chunks: 8,
        status: "protected",
        uploadedAt: "2026-07-30 10:30",
      },
    ];
  });

  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isBulkIngesting, setIsBulkIngesting] = useState<boolean>(false);
  const [bulkIngestResult, setBulkIngestResult] = useState<BulkIngestResponse | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const saveDocuments = (docs: DocumentItem[]) => {
    setDocuments(docs);
    try {
      localStorage.setItem("sentinel_documents", JSON.stringify(docs));
    } catch {
      // fallback
    }
  };

  const uploadFile = useCallback(async (file: File, classification: "public" | "confidential") => {
    setIsUploading(true);
    setNotification(null);

    const tempId = `doc-${Date.now()}`;
    const newDoc: DocumentItem = {
      id: tempId,
      name: file.name,
      classification,
      documentType: "processing...",
      chunks: 0,
      status: "uploading",
      uploadedAt: new Date().toISOString().replace("T", " ").slice(0, 16),
    };

    saveDocuments([newDoc, ...documents]);

    try {
      const res: UploadResponse = await documentsApi.upload(file, classification);

      const updatedDoc: DocumentItem = {
        id: tempId,
        name: res.filename,
        classification: (res.classification.toLowerCase() as "public" | "confidential") || classification,
        documentType: res.classification === "confidential" ? "protected" : "public",
        chunks: res.chunks,
        status: res.classification === "confidential" ? "protected" : "indexed",
        uploadedAt: new Date().toISOString().replace("T", " ").slice(0, 16),
      };

      setDocuments((prev) => {
        const next = prev.map((d) => (d.id === tempId ? updatedDoc : d));
        localStorage.setItem("sentinel_documents", JSON.stringify(next));
        return next;
      });

      setNotification({
        type: "success",
        message: `Successfully ingested '${res.filename}' into vector store (${res.chunks} chunks).`,
      });
    } catch (err: any) {
      setDocuments((prev) => {
        const next = prev.map((d) => (d.id === tempId ? { ...d, status: "failed" as const } : d));
        localStorage.setItem("sentinel_documents", JSON.stringify(next));
        return next;
      });

      setNotification({
        type: "error",
        message: err.message || `Failed to upload and ingest '${file.name}'.`,
      });
    } finally {
      setIsUploading(false);
    }
  }, [documents]);

  const triggerBulkIngest = useCallback(async () => {
    setIsBulkIngesting(true);
    setNotification(null);
    setBulkIngestResult(null);

    try {
      const res: BulkIngestResponse = await documentsApi.bulkIngest();
      setBulkIngestResult(res);

      setNotification({
        type: "success",
        message: `Bulk ingestion complete: Processed ${res.documents_processed} documents (${res.total_chunks} text chunks stored in ChromaDB).`,
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Failed to trigger bulk knowledge base ingestion.",
      });
    } finally {
      setIsBulkIngesting(false);
    }
  }, []);

  return {
    documents,
    isUploading,
    isBulkIngesting,
    bulkIngestResult,
    notification,
    uploadFile,
    triggerBulkIngest,
    clearNotification: () => setNotification(null),
  };
}
