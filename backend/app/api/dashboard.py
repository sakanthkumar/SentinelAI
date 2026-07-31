"""Dashboard & System Telemetry API endpoint module for SentinelAI platform."""

import logging
from typing import Any

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & Telemetry"])
_dashboard_service = DashboardService()


class DocumentDetail(BaseModel):
    """Schema for individual document item details."""

    name: str = Field(..., example="financial_report_q2_2026.pdf", description="Filename")
    classification: str = Field(..., example="confidential", description="Security classification")
    indexed: bool = Field(True, description="Whether document is indexed in ChromaDB")
    source: str = Field(..., example="Documents/confidential/financial_report_q2_2026.pdf", description="Relative file path")
    chunks: int = Field(..., example=32, description="Vector text chunks count")


class DashboardStatsResponse(BaseModel):
    """Response schema for real dashboard metrics."""

    total_documents: int = Field(..., example=3, description="Total knowledge documents in storage")
    public_documents: int = Field(..., example=1, description="Count of public classification documents")
    confidential_documents: int = Field(..., example=2, description="Count of confidential classification documents")
    protected_documents: int = Field(..., example=2, description="Count of protected vault documents")
    protected_chunks: int = Field(..., example=64, description="Total text chunks stored in protected vault")
    vault_health: str = Field("Healthy", example="Healthy", description="Status of protected_vault collection")
    blocked_requests: int = Field(..., example=0, description="Real count of blocked requests")
    allowed_requests: int = Field(..., example=0, description="Real count of allowed requests")


class SystemHealthResponse(BaseModel):
    """Schema for system component health telemetry."""

    fastapi: str = Field("Healthy", example="Healthy", description="FastAPI server health")
    chromadb: str = Field("Healthy", example="Healthy", description="ChromaDB vector store health")
    llm: str = Field("Healthy", example="Healthy", description="LLM provider connection health")
    policy_engine: str = Field("Healthy", example="Healthy", description="DLP PolicyEngine status")
    semantic_dlp: str = Field("Healthy", example="Healthy", description="Semantic DLP Detector status")
    overall_status: str = Field("Healthy", example="Healthy", description="Overall platform operational status")


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Statistics",
    description="Retrieve live metric counts and protected vault telemetry.",
)
def get_dashboard_stats(request: Request) -> DashboardStatsResponse:
    """Return real metrics computed from system state and vector store."""
    logger.info("Received request for dashboard statistics")
    stats = _dashboard_service.get_stats(request)
    return DashboardStatsResponse(**stats)


@router.get(
    "/documents",
    response_model=list[DocumentDetail],
    status_code=status.HTTP_200_OK,
    summary="Get Protected Documents List",
    description="Retrieve list of documents indexed in public or confidential vector store.",
)
def get_dashboard_documents(request: Request) -> list[DocumentDetail]:
    """Return list of actual documents from ChromaDB vector store."""
    logger.info("Received request for dashboard documents list")
    docs_raw = _dashboard_service.get_documents_list(request)
    return [
        DocumentDetail(
            name=d["name"],
            classification=d["classification"],
            indexed=d["indexed"],
            source=d["source"],
            chunks=d["chunks"],
        )
        for d in docs_raw
    ]


@router.get(
    "/events",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Security Audit Events",
    description="Retrieve live security evaluation audit events from persistent backend audit log.",
)
def get_dashboard_events(
    request: Request,
    limit: int = 50,
    decision: str | None = None,
    severity: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """Return filtered security audit events log."""
    logger.info("Received request for security audit events")
    try:
        audit_logger = getattr(request.app.state, "audit_logger", None)
        if audit_logger:
            return audit_logger.get_events(
                limit=limit,
                decision=decision,
                severity=severity,
                search_query=search,
            )
    except Exception as exc:
        logger.error("Failed to retrieve audit events: %s", exc)
    return []


@router.get(
    "/system-health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health Telemetry",
    description="Retrieve operational health status across core system components.",
)
def get_system_health(request: Request) -> SystemHealthResponse:
    """Return health status of FastAPI, ChromaDB, LLM, PolicyEngine, and Semantic DLP."""
    logger.info("Received request for system component health telemetry")
    health = _dashboard_service.get_system_health(request)
    return SystemHealthResponse(**health)
