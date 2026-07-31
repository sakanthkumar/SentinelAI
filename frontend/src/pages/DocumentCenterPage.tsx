import React, { useState } from "react";
import {
  Upload,
  FileText,
  Lock,
  Globe,
  CheckCircle2,
  AlertCircle,
  Database,
  RefreshCw,
  FolderPlus,
  Loader2,
  Search,
  Inbox,
  Trash2,
  X,
  FileUp,
} from "lucide-react";
import { useUpload } from "../hooks/useUpload";
import type { DocumentDetail } from "../types";

export const DocumentCenterPage: React.FC = () => {
  const {
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
    refreshDocuments,
    clearNotification,
  } = useUpload();

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [classification, setClassification] = useState<"public" | "confidential">("public");
  const [isDragging, setIsDragging] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const [docToDelete, setDocToDelete] = useState<DocumentDetail | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0 || isUploading) return;

    if (selectedFiles.length === 1) {
      await uploadFile(selectedFiles[0], classification);
    } else {
      await bulkUpload(selectedFiles, classification);
    }
    setSelectedFiles([]);
  };

  const confirmDelete = async () => {
    if (!docToDelete) return;
    await deleteDocument(docToDelete.id);
    setDocToDelete(null);
  };

  const filteredDocs = documents.filter((doc) =>
    doc.name.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes === 0) return "N/A";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Document Management Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
              ChromaDB Storage
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ingest, manage, and delete enterprise documents with automatic vector embedding purging and file cleanup.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={refreshDocuments}
            disabled={isLoadingDocs}
            aria-label="Refresh Documents List"
            title="Refresh Documents List"
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingDocs ? "animate-spin" : ""}`} aria-hidden="true" />
          </button>

          {/* Bulk Ingest Directory Trigger */}
          <button
            onClick={triggerBulkIngest}
            disabled={isBulkIngesting}
            aria-label="Ingest Knowledge Base Directory"
            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-purple-500/25 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {isBulkIngesting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Bulk Ingesting Directory...</span>
              </>
            ) : (
              <>
                <FolderPlus className="w-4 h-4" aria-hidden="true" />
                <span>Ingest Knowledge Base Directory</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium ${
            notification.type === "success"
              ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-200"
              : "bg-rose-950/60 border-rose-800/80 text-rose-200"
          }`}
        >
          <div className="flex items-center space-x-2">
            {notification.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden="true" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" aria-hidden="true" />
            )}
            <span>{notification.message}</span>
          </div>
          <button onClick={clearNotification} className="text-slate-400 hover:text-white focus:outline-none">
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Bulk Ingest Summary Breakdown Card */}
      {bulkIngestResult && (
        <div className="bg-slate-900 border border-purple-900/60 p-5 rounded-2xl space-y-3">
          <h3 className="text-sm font-bold text-purple-300 flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-400" aria-hidden="true" />
            Directory Ingestion Summary
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Documents Processed</span>
              <span className="text-lg font-bold text-white">{bulkIngestResult.documents_processed}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Public Documents</span>
              <span className="text-lg font-bold text-cyan-400">{bulkIngestResult.public_documents}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Confidential Vault Docs</span>
              <span className="text-lg font-bold text-purple-400">{bulkIngestResult.confidential_documents}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Total Text Chunks Stored</span>
              <span className="text-lg font-bold text-emerald-400">{bulkIngestResult.total_chunks}</span>
            </div>
          </div>
        </div>
      )}

      {/* Two Columns: Upload & Multi-File Queue (Left) & Document Directory Table (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form Box */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <FileUp className="w-4 h-4 text-cyan-400" aria-hidden="true" />
            Upload & Ingest Documents
          </h2>

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            {/* Classification Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Target Knowledge Classification:
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setClassification("public")}
                  aria-label="Select Public Classification"
                  className={`p-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 ${
                    classification === "public"
                      ? "bg-cyan-950/80 border-cyan-500 text-cyan-300 shadow-md shadow-cyan-950/50"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <Globe className="w-4 h-4 text-cyan-400" aria-hidden="true" />
                  <span>Public KB</span>
                </button>

                <button
                  type="button"
                  onClick={() => setClassification("confidential")}
                  aria-label="Select Confidential Classification"
                  className={`p-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition-all focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                    classification === "confidential"
                      ? "bg-purple-950/80 border-purple-500 text-purple-300 shadow-md shadow-purple-950/50"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <Lock className="w-4 h-4 text-purple-400" aria-hidden="true" />
                  <span>Protected Vault</span>
                </button>
              </div>
            </div>

            {/* Drag & Drop Multi-File Select */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`p-6 border-2 border-dashed rounded-2xl text-center transition-all cursor-pointer ${
                isDragging
                  ? "border-cyan-400 bg-cyan-950/20"
                  : selectedFiles.length > 0
                  ? "border-emerald-500/60 bg-emerald-950/10"
                  : "border-slate-700 hover:border-slate-600 bg-slate-950/60"
              }`}
            >
              <input
                type="file"
                multiple
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
                id="multi-file-input"
              />
              <label htmlFor="multi-file-input" className="cursor-pointer space-y-2 block">
                <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                  <Upload className="w-5 h-5 text-cyan-400" aria-hidden="true" />
                </div>
                {selectedFiles.length > 0 ? (
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-emerald-400">
                      {selectedFiles.length} file(s) selected
                    </p>
                    <p className="text-[10px] text-slate-400">
                      Total size: {(selectedFiles.reduce((acc, f) => acc + f.size, 0) / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-200">
                      Drag & Drop PDF/DOCX files or folders
                    </p>
                    <p className="text-[10px] text-slate-400">Select multiple files for batch upload & ingest</p>
                  </div>
                )}
              </label>
            </div>

            {/* Selected File Queue List */}
            {selectedFiles.length > 0 && (
              <div className="max-h-32 overflow-y-auto space-y-1 bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                {selectedFiles.map((f, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[11px] text-slate-300 px-2 py-1 bg-slate-900/60 rounded">
                    <span className="truncate max-w-[180px] font-mono">{f.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{(f.size / 1024).toFixed(0)} KB</span>
                  </div>
                ))}
              </div>
            )}

            <button
              type="submit"
              disabled={selectedFiles.length === 0 || isUploading}
              aria-label="Upload & Ingest Selected Files"
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Uploading & Ingesting Chunks...</span>
                </>
              ) : (
                <span>Upload & Start Ingestion ({selectedFiles.length})</span>
              )}
            </button>
          </form>
        </div>

        {/* Documents Directory Table */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" aria-hidden="true" />
              Document Inventory List
            </h2>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" aria-hidden="true" />
              <input
                type="text"
                placeholder="Filter documents..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                aria-label="Filter documents by name"
                className="bg-slate-950 text-slate-200 text-xs rounded-lg pl-8 pr-3 py-1.5 border border-slate-800 focus:outline-none focus:border-cyan-500/60"
              />
            </div>
          </div>

          {filteredDocs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse" aria-label="Indexed Documents Directory Table">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950">
                    <th className="py-2.5 px-3">Document Name</th>
                    <th className="py-2.5 px-3">Classification</th>
                    <th className="py-2.5 px-3">Chunks</th>
                    <th className="py-2.5 px-3">Size</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3 font-semibold text-slate-200">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
                          <span className="truncate max-w-[180px]" title={doc.name}>
                            {doc.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${
                            doc.classification === "confidential"
                              ? "bg-purple-950 text-purple-300 border border-purple-800/60"
                              : "bg-cyan-950 text-cyan-300 border border-cyan-800/60"
                          }`}
                        >
                          {doc.classification === "confidential" ? (
                            <Lock className="w-2.5 h-2.5" aria-hidden="true" />
                          ) : (
                            <Globe className="w-2.5 h-2.5" aria-hidden="true" />
                          )}
                          <span>{doc.classification}</span>
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-slate-300">{doc.chunks}</td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-400">{formatBytes(doc.size_bytes)}</td>
                      <td className="py-3 px-3">
                        {doc.classification === "confidential" ? (
                          <span className="text-purple-400 font-semibold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Protected Vault
                          </span>
                        ) : (
                          <span className="text-cyan-400 font-semibold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Public KB
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => setDocToDelete(doc)}
                          disabled={isDeletingId === doc.id}
                          aria-label={`Delete ${doc.name}`}
                          className="px-2.5 py-1 bg-rose-950/80 hover:bg-rose-900 text-rose-300 rounded-lg border border-rose-800/60 text-xs font-medium transition-colors inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-rose-500"
                        >
                          {isDeletingId === doc.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
                          ) : (
                            <Trash2 className="w-3 h-3 text-rose-400" aria-hidden="true" />
                          )}
                          <span>Delete</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
              <Inbox className="w-8 h-8 text-slate-600" aria-hidden="true" />
              <p className="text-xs font-semibold text-slate-400">No Documents Found</p>
              <p className="text-[11px] text-slate-500 max-w-xs">
                Upload files using the multi-file uploader or click "Ingest Knowledge Base Directory".
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {docToDelete && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-rose-950/80 text-rose-400 border border-rose-800/60 rounded-xl">
                  <Trash2 className="w-5 h-5" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Confirm Document Deletion</h3>
                  <p className="text-xs text-slate-400">Permanently purge vectors and physical file</p>
                </div>
              </div>
              <button
                onClick={() => setDocToDelete(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg focus:outline-none"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>

            <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Filename:</span>
                <span className="font-bold text-white font-mono truncate max-w-[200px]">{docToDelete.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Classification:</span>
                <span className="font-semibold text-cyan-400 uppercase font-mono">{docToDelete.classification}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Vector Chunks:</span>
                <span className="font-semibold text-purple-400 font-mono">{docToDelete.chunks} chunks</span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to delete <span className="font-semibold text-rose-300">{docToDelete.name}</span>? This will permanently remove the physical file from disk and purge all associated vector embeddings from ChromaDB.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setDocToDelete(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 transition-colors focus:outline-none"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={isDeletingId === docToDelete.id}
                className="px-5 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-rose-600/30 transition-all flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-rose-500"
              >
                {isDeletingId === docToDelete.id ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                    <span>Deleting Document...</span>
                  </>
                ) : (
                  <span>Delete Document</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
