/**
 * Custom hook for managing document upload queue, multi-file bulk ingestion, and single-click deletion.
 */

import { useCallback, useEffect, useState } from "react";
import { documentsApi } from "../services/api";
import type { BulkIngestResponse, DocumentDetail } from "../types";

export function useUpload() {
  const [documents, setDocuments] = useState<DocumentDetail[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [isBulkIngesting, setIsBulkIngesting] = useState<boolean>(false);
  const [bulkIngestResult, setBulkIngestResult] = useState<BulkIngestResponse | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await documentsApi.list();
      if (Array.isArray(data)) {
        setDocuments(data);
      }
    } catch (err: any) {
      logger_fallback(err);
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  function logger_fallback(err: any) {
    // Silent fallback
  }

  const uploadFile = useCallback(
    async (file: File, classification: "public" | "confidential") => {
      setIsUploading(true);
      setNotification(null);

      try {
        const res = await documentsApi.upload(file, classification);
        await fetchDocuments();
        setNotification({
          type: "success",
          message: `Successfully ingested '${res.filename}' into vector store (${res.chunks} chunks).`,
        });
      } catch (err: any) {
        setNotification({
          type: "error",
          message: err.message || `Failed to upload and ingest '${file.name}'.`,
        });
      } finally {
        setIsUploading(false);
      }
    },
    [fetchDocuments]
  );

  const bulkUpload = useCallback(
    async (files: File[], classification: "public" | "confidential") => {
      setIsUploading(true);
      setNotification(null);

      try {
        const res = await documentsApi.bulkUpload(files, classification);
        await fetchDocuments();
        const successCount = res.successful || 0;
        const failCount = res.failed || 0;

        if (failCount === 0) {
          setNotification({
            type: "success",
            message: `Successfully ingested ${successCount} document(s) into vector store.`,
          });
        } else {
          setNotification({
            type: "error",
            message: `Bulk upload completed: ${successCount} succeeded, ${failCount} failed. Check document list for details.`,
          });
        }
        return res;
      } catch (err: any) {
        setNotification({
          type: "error",
          message: err.message || "Failed to execute multi-file bulk upload.",
        });
      } finally {
        setIsUploading(false);
      }
    },
    [fetchDocuments]
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      setIsDeletingId(documentId);
      setNotification(null);

      try {
        const res = await documentsApi.deleteDocument(documentId);
        await fetchDocuments();
        setNotification({
          type: "success",
          message: res.message || `Document deleted successfully and vectors purged from ChromaDB.`,
        });
      } catch (err: any) {
        setNotification({
          type: "error",
          message: err.message || `Failed to delete document '${documentId}'.`,
        });
      } finally {
        setIsDeletingId(null);
      }
    },
    [fetchDocuments]
  );

  const triggerBulkIngest = useCallback(async () => {
    setIsBulkIngesting(true);
    setNotification(null);
    setBulkIngestResult(null);

    try {
      const res: BulkIngestResponse = await documentsApi.bulkIngest();
      setBulkIngestResult(res);
      await fetchDocuments();

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
  }, [fetchDocuments]);

  return {
    documents,
    isLoadingDocs,
    isUploading,
    isDeletingId,
    isBulkIngesting,
    bulkIngestResult,
    notification,
    uploadFile,
    bulkUpload,
    deleteDocument,
    triggerBulkIngest,
    refreshDocuments: fetchDocuments,
    clearNotification: () => setNotification(null),
  };
}
