"""SentinelAI Enterprise AI Security Platform REST API Application.

Main entrypoint configuring FastAPI, registering health, upload, chat, and knowledge base routers,
and initializing singletons via lifespan dependency management.
"""

from app.detection.similarity_detector import SimilarityDetector
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
import uvicorn

from app.ai.rag_pipeline import RAGPipeline
from app.ai.retriever import Retriever
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.upload import router as upload_router
from app.detection.leak_detector import LeakDetector
from app.llm.factory import LLMFactory
from app.detection.similarity_detector import SimilarityDetector
from app.services.chunking import TextChunker
from app.services.document_loader import DocumentLoader
from app.services.embeddings import EmbeddingService
from app.services.ingestion import IngestionService
from app.services.vector_store import VectorStore

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SentinelAI")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle and initialize singletons on startup.

    Initialization order:
    EmbeddingService -> VectorStore -> Retriever -> LLMFactory -> BaseLLM -> LeakDetector -> RAGPipeline -> IngestionService
    """
    logger.info("Initializing SentinelAI core backend services...")

    try:
        # 1. EmbeddingService
        embedding_service = EmbeddingService()

        # 2. VectorStore
        vector_store = VectorStore()

        # 3. Retriever
        retriever = Retriever(
            embedding_service=embedding_service,
            vector_store=vector_store,
        )

        # 4. LLMFactory -> BaseLLM
        llm = LLMFactory.get_provider()
        protected_vault = VectorStore(collection_name="protected_vault")
        
        # 5. Shared SimilarityDetector
        similarity_detector = SimilarityDetector(
            embedding_service=embedding_service,
            vector_store=VectorStore(collection_name="protected_vault"),
        )

        # 6. LeakDetector
        leak_detector = LeakDetector(
            similarity_detector=similarity_detector,
)

        # 6. RAGPipeline with injected LeakDetector
        rag_pipeline = RAGPipeline(
            retriever=retriever,
            llm=llm,
            leak_detector=leak_detector,
        )

        # 7. IngestionService
        ingestion_service = IngestionService(
            loader=DocumentLoader(),
            chunker=TextChunker(),
            embedding_service=embedding_service,
            vector_store=vector_store,
        )

        # Store singletons in application state for dependency injection across requests
        app.state.embedding_service = embedding_service
        app.state.vector_store = vector_store
        app.state.retriever = retriever
        app.state.llm = llm
        app.state.leak_detector = leak_detector
        app.state.rag_pipeline = rag_pipeline
        app.state.ingestion_service = ingestion_service

        logger.info("SentinelAI core services initialized successfully.")

    except Exception as exc:
        logger.error("Failed to initialize SentinelAI core backend services: %s", exc)
        # Allow application to boot while logging initialization warning if environment restrictions apply
        pass

    yield

    logger.info("Shutting down SentinelAI application services.")


import os
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SentinelAI",
    description="Enterprise AI Security and RAG Platform REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Dynamic CORS origins configuration from environment
cors_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
if "*" not in allowed_origins:
    allowed_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.dashboard import router as dashboard_router

# Register REST API routers
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(knowledge_base_router)
app.include_router(dashboard_router)

# Global production exception handler preventing stack trace disclosure
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled server error processing request %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred while processing the request.",
            "path": request.url.path,
        },
    )


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Root endpoint for basic verification."""
    return {
        "status": "running",
        "project": "SentinelAI",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)