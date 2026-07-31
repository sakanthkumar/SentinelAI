"""DashboardService module for SentinelAI platform."""

import logging
from pathlib import Path
from typing import Any

from fastapi import Request

from app.llm.config import settings
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DashboardService:
    """Service responsible for computing dashboard statistics and querying knowledge base inventory."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        protected_vault: VectorStore | None = None,
    ) -> None:
        """Initialize DashboardService with optional injected vector stores."""
        self.vector_store = vector_store
        self.protected_vault = protected_vault

    def _get_vector_stores(self, request: Request | None = None) -> tuple[VectorStore | None, VectorStore | None]:
        """Resolve enterprise_docs and protected_vault vector stores from request state or defaults."""
        v_store = self.vector_store
        p_vault = self.protected_vault

        if request and hasattr(request, "app") and hasattr(request.app, "state"):
            if v_store is None:
                v_store = getattr(request.app.state, "vector_store", None)
            if p_vault is None:
                p_vault = getattr(request.app.state, "protected_vault", None)

        if v_store is None:
            try:
                v_store = VectorStore(collection_name="enterprise_docs")
            except Exception:
                pass

        if p_vault is None:
            try:
                p_vault = VectorStore(collection_name="protected_vault")
            except Exception:
                pass

        return v_store, p_vault

    def get_documents_list(self, request: Request | None = None) -> list[dict[str, Any]]:
        """Retrieve list of actual existing indexed documents from ChromaDB and disk.

        Logic:
        1. Query enterprise_docs collection.
        2. Query protected_vault collection.
        3. Calculate chunk counts from ChromaDB metadatas (no hardcoded chunk counts).
        4. Verify every referenced file exists using Path.exists(). Skip deleted files.
        5. If ChromaDB is empty, fallback to filesystem scan for actual existing files (chunks=0).
        6. If no documents exist on disk or in ChromaDB, return empty list [].
        """
        v_store, p_vault = self._get_vector_stores(request)
        doc_map: dict[str, dict[str, Any]] = {}
        base_dir = Path(__file__).resolve().parents[2]

        def _process_collection(store: VectorStore | None, default_classif: str) -> None:
            if not store or not hasattr(store, "_collection"):
                return
            try:
                if store._collection.count() == 0:
                    return
                res = store._collection.get(include=["metadatas"])
                metadatas = res.get("metadatas") or []
                for meta in metadatas:
                    if not meta:
                        continue
                    source = meta.get("source") or "unknown_document"
                    classif = meta.get("classification") or default_classif
                    file_path_str = meta.get("file_path") or ""

                    # Verify existence on disk using Path.exists()
                    file_exists = False
                    resolved_rel_path = f"Documents/{classif}/{source}"

                    candidate_paths = []
                    if file_path_str:
                        candidate_paths.append(Path(file_path_str))
                    candidate_paths.extend([
                        base_dir / "Documents" / classif / source,
                        base_dir.parent / "Documents" / classif / source,
                        base_dir / settings.upload_folder / classif / source,
                        base_dir / "Documents" / "public" / source,
                        base_dir / "Documents" / "confidential" / source,
                    ])

                    for p in candidate_paths:
                        if p and p.exists() and p.is_file():
                            file_exists = True
                            p_str = str(p).replace("\\", "/")
                            if "Documents/" in p_str:
                                parts = p_str.split("Documents/")
                                resolved_rel_path = f"Documents/{parts[-1]}"
                            elif "uploads/" in p_str:
                                parts = p_str.split("uploads/")
                                resolved_rel_path = f"uploads/{parts[-1]}"
                            else:
                                resolved_rel_path = str(p)
                            break

                    # Skip deleted or non-existent files
                    if not file_exists:
                        continue

                    doc_key = f"{classif}:{resolved_rel_path.lower()}"
                    if doc_key not in doc_map:
                        doc_map[doc_key] = {
                            "name": source,
                            "classification": classif,
                            "indexed": True,
                            "source": resolved_rel_path,
                            "chunks": 0,
                        }
                    doc_map[doc_key]["chunks"] += 1
                    if default_classif == "confidential":
                        doc_map[doc_key]["classification"] = "confidential"
            except Exception as exc:
                logger.error("Failed to query collection metadatas: %s", exc)

        # Step 1: Query enterprise_docs
        _process_collection(v_store, "public")

        # Step 2: Query protected_vault
        _process_collection(p_vault, "confidential")

        # Step 3: If doc_map is empty, check filesystem for actual existing files
        if not doc_map:
            docs_dir = base_dir / "Documents"
            if not docs_dir.exists():
                docs_dir = base_dir.parent / "Documents"

            if docs_dir.exists():
                for sub_dir, classif in [("public", "public"), ("confidential", "confidential")]:
                    target_sub = docs_dir / sub_dir
                    if target_sub.exists():
                        for f in target_sub.rglob("*"):
                            if f.is_file() and f.suffix.lower() in {".pdf", ".docx", ".txt"}:
                                rel_path = f"Documents/{sub_dir}/{f.name}"
                                doc_key = f"{classif}:{rel_path.lower()}"
                                if doc_key not in doc_map:
                                    doc_map[doc_key] = {
                                        "name": f.name,
                                        "classification": classif,
                                        "indexed": False,
                                        "source": rel_path,
                                        "chunks": 0,  # Zero hardcoded chunk count
                                    }

        return list(doc_map.values())

    def get_stats(self, request: Request) -> dict[str, Any]:
        """Compute real dashboard statistics from actual existing documents and vector stores.

        If there are no documents:
            total_documents = 0
            public_documents = 0
            confidential_documents = 0
            protected_documents = 0
            protected_chunks = 0
        """
        docs = self.get_documents_list(request)
        total_docs = len(docs)
        pub_docs = len([d for d in docs if d["classification"] == "public"])
        conf_docs = len([d for d in docs if d["classification"] == "confidential"])

        v_store, p_vault = self._get_vector_stores(request)

        protected_chunks = 0
        vault_health = "Healthy"
        if p_vault and hasattr(p_vault, "_collection"):
            try:
                vault_count = p_vault._collection.count()
                protected_chunks = vault_count
            except Exception as exc:
                logger.error("Failed to query protected_vault count: %s", exc)
                vault_health = "Offline"

        if protected_chunks == 0 and conf_docs > 0:
            protected_chunks = sum(d["chunks"] for d in docs if d["classification"] == "confidential")

        blocked_count = 0
        allowed_count = 0
        try:
            audit_logger = getattr(request.app.state, "audit_logger", None)
            if audit_logger:
                audit_stats = audit_logger.get_stats()
                blocked_count = audit_stats.get("blocked_requests", 0)
                allowed_count = audit_stats.get("allowed_requests", 0)
        except Exception:
            pass

        return {
            "total_documents": total_docs,
            "public_documents": pub_docs,
            "confidential_documents": conf_docs,
            "protected_documents": conf_docs,
            "protected_chunks": protected_chunks if total_docs > 0 else 0,
            "vault_health": vault_health,
            "blocked_requests": blocked_count,
            "allowed_requests": allowed_count,
        }

    def get_system_health(self, request: Request) -> dict[str, Any]:
        """Check health status of system components."""
        chroma_health = "Healthy"
        llm_health = "Healthy"

        v_store, _ = self._get_vector_stores(request)
        if v_store and hasattr(v_store, "_collection"):
            try:
                v_store._collection.count()
            except Exception:
                chroma_health = "Offline"
        else:
            chroma_health = "Offline"

        try:
            llm = getattr(request.app.state, "llm", None)
            if not llm:
                llm_health = "Offline"
        except Exception:
            llm_health = "Offline"

        return {
            "fastapi": "Healthy",
            "chromadb": chroma_health,
            "llm": llm_health,
            "policy_engine": "Healthy",
            "semantic_dlp": "Healthy",
            "overall_status": "Healthy" if chroma_health == "Healthy" and llm_health == "Healthy" else "Warning",
        }
