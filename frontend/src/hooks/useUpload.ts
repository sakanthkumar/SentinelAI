/**
 * Custom hook for managing document upload queue, multi-file ingestion, and single-click deletion.
 */

import { useCallback, useEffect, useState } from "react";
import { documentsApi } from "../services/api";
import type { DocumentDetail } from "../types";

export function useUpload(onSuccessCallback?: () => void) {
  const [documents, setDocuments] = useState<DocumentDetail[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await documentsApi.list();
      if (Array.isArray(data)) {
        setDocuments(data);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const uploadFiles = useCallback(
    async (files: File | File[], classification: "public" | "confidential") => {
      setIsUploading(true);
      setNotification(null);

      const fileArray = Array.isArray(files) ? files : [files];

      try {
        const res = await documentsApi.upload(fileArray, classification);
        await fetchDocuments();
        if (onSuccessCallback) onSuccessCallback();

        const successCount = res.successful ?? res.processed ?? 1;
        const failCount = res.failed ?? 0;
        const total = res.processed ?? fileArray.length;

        if (failCount === 0) {
          if (total === 1 && res.results?.[0]?.filename) {
            setNotification({
              type: "success",
              message: `Uploaded '${res.results[0].filename}' successfully (${res.results[0].chunks} vector chunks stored).`,
            });
          } else {
            setNotification({
              type: "success",
              message: `Uploaded ${successCount} document(s) successfully.`,
            });
          }
        } else {
          setNotification({
            type: "error",
            message: `Uploaded ${total} document(s): ${successCount} succeeded, ${failCount} failed.`,
          });
        }
        return res;
      } catch (err: any) {
        setNotification({
          type: "error",
          message: err.message || "Failed to complete document upload and ingestion.",
        });
      } finally {
        setIsUploading(false);
      }
    },
    [fetchDocuments, onSuccessCallback]
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      setIsDeletingId(documentId);
      setNotification(null);

      try {
        const res = await documentsApi.deleteDocument(documentId);
        await fetchDocuments();
        if (onSuccessCallback) onSuccessCallback();

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
    [fetchDocuments, onSuccessCallback]
  );

  return {
    documents,
    isLoadingDocs,
    isUploading,
    isDeletingId,
    notification,
    uploadFiles,
    deleteDocument,
    refreshDocuments: fetchDocuments,
    clearNotification: () => setNotification(null),
  };
}
