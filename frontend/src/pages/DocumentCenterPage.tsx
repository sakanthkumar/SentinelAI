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
} from "lucide-react";
import { useUpload } from "../hooks/useUpload";

export const DocumentCenterPage: React.FC = () => {
  const {
    documents,
    isUploading,
    isBulkIngesting,
    bulkIngestResult,
    notification,
    uploadFile,
    triggerBulkIngest,
    clearNotification,
  } = useUpload();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [classification, setClassification] = useState<"public" | "confidential">("public");
  const [isDragging, setIsDragging] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
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
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || isUploading) return;
    uploadFile(selectedFile, classification);
    setSelectedFile(null);
  };

  const filteredDocs = documents.filter((doc) =>
    doc.name.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Document Ingestion Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
              ChromaDB Store
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ingest enterprise documents with automatic classification into public knowledge base or protected vault.
          </p>
        </div>

        {/* Bulk Knowledge Base Ingestion Trigger Button */}
        <button
          onClick={triggerBulkIngest}
          disabled={isBulkIngesting}
          aria-label="Ingest Knowledge Base Directory"
          className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-purple-500/25 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {isBulkIngesting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              <span>Bulk Ingesting Documents...</span>
            </>
          ) : (
            <>
              <FolderPlus className="w-4 h-4" aria-hidden="true" />
              <span>Ingest Knowledge Base Directory</span>
            </>
          )}
        </button>
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
            Dismiss
          </button>
        </div>
      )}

      {/* Bulk Ingest Result Breakdown Card */}
      {bulkIngestResult && (
        <div className="bg-slate-900 border border-purple-900/60 p-5 rounded-2xl space-y-3">
          <h3 className="text-sm font-bold text-purple-300 flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-400" aria-hidden="true" />
            Bulk Ingestion Execution Summary
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

      {/* Two Columns: File Uploader Form (Left) & Document Directory Table (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Upload Box */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Upload className="w-4 h-4 text-cyan-400" aria-hidden="true" />
            Upload Single Document
          </h2>

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            {/* Classification Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Security Classification:
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
                  <span>Public Document</span>
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
                  <span>Confidential Vault</span>
                </button>
              </div>
            </div>

            {/* Drag & Drop Target Area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`p-6 border-2 border-dashed rounded-2xl text-center transition-all cursor-pointer ${
                isDragging
                  ? "border-cyan-400 bg-cyan-950/20"
                  : selectedFile
                  ? "border-emerald-500/60 bg-emerald-950/10"
                  : "border-slate-700 hover:border-slate-600 bg-slate-950/60"
              }`}
            >
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
                id="file-input"
              />
              <label htmlFor="file-input" className="cursor-pointer space-y-2 block">
                <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                  <Upload className="w-5 h-5 text-cyan-400" aria-hidden="true" />
                </div>
                {selectedFile ? (
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-emerald-400 truncate max-w-[200px] mx-auto">
                      {selectedFile.name}
                    </p>
                    <p className="text-[10px] text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-200">
                      Drag & Drop PDF or DOCX file here
                    </p>
                    <p className="text-[10px] text-slate-400">or click to browse filesystem</p>
                  </div>
                )}
              </label>
            </div>

            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              aria-label="Upload and Ingest Vector Chunks"
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Processing & Embedding...</span>
                </>
              ) : (
                <span>Upload & Ingest Vector Chunks</span>
              )}
            </button>
          </form>
        </div>

        {/* Documents Directory Table (2 Cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" aria-hidden="true" />
              Indexed Documents List
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
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Ingested At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3 font-semibold text-slate-200 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
                        <span className="truncate max-w-[200px]">{doc.name}</span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${
                            doc.classification === "confidential"
                              ? "bg-purple-950 text-purple-300 border border-purple-800/60"
                              : "bg-cyan-950 text-cyan-300 border border-cyan-800/60"
                          }`}
                        >
                          {doc.classification === "confidential" ? <Lock className="w-2.5 h-2.5" aria-hidden="true" /> : <Globe className="w-2.5 h-2.5" aria-hidden="true" />}
                          <span>{doc.classification}</span>
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-slate-300">{doc.chunks}</td>
                      <td className="py-3 px-3">
                        {doc.status === "protected" && (
                          <span className="text-purple-400 font-semibold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Protected Vault
                          </span>
                        )}
                        {doc.status === "indexed" && (
                          <span className="text-cyan-400 font-semibold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Public Repository
                          </span>
                        )}
                        {doc.status === "uploading" && (
                          <span className="text-amber-400 font-semibold text-[11px] flex items-center gap-1">
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" aria-hidden="true" /> Ingesting...
                          </span>
                        )}
                        {doc.status === "failed" && (
                          <span className="text-rose-400 font-semibold text-[11px] flex items-center gap-1">
                            <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" /> Ingestion Failed
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">{doc.uploadedAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
              <Inbox className="w-8 h-8 text-slate-600" aria-hidden="true" />
              <p className="text-xs font-semibold text-slate-400">No Documents Uploaded</p>
              <p className="text-[11px] text-slate-500 max-w-xs">
                Upload files using the single file form or click "Ingest Knowledge Base Directory".
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
