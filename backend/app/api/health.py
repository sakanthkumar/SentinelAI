"""Health check API endpoint module for SentinelAI platform."""

import logging
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response schema for system health check endpoint."""

    status: str = Field(..., example="running", description="Operational status of the service")
    project: str = Field(..., example="SentinelAI", description="Name of the project")
    version: str = Field(..., example="1.0.0", description="API version")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the operational status of the SentinelAI REST API platform.",
)
async def get_health() -> HealthResponse:
    """Return operational health status of SentinelAI platform."""
    logger.info("Health check endpoint invoked")
    return HealthResponse(
        status="running",
        project="SentinelAI",
        version="1.0.0",
    )
