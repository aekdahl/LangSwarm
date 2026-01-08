from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..auth import get_current_user, User
from ...core.rag.optimizer import RAGOptimizer
from ...core.rag.pipeline import IngestionPipeline
# from ...core.memory.hybrid import HybridMemoryManager # Dependency injection needed in real app

router = APIRouter()

# Global instances for now (in production, use dependency injection)
optimizer = RAGOptimizer()
# ingestion_pipeline = IngestionPipeline(memory_manager=...) # Needs configured manager

class OptimizationRequest(BaseModel):
    documents: List[str]

class RerankRequest(BaseModel):
    query: str
    documents: List[Dict[str, Any]]

class IngestionRequest(BaseModel):
    path: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/optimize/summarize")
async def summarize_documents(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Summarize a list of documents."""
    return await optimizer.summarize(request.documents)

@router.post("/optimize/rerank")
async def rerank_documents(
    request: RerankRequest,
    current_user: User = Depends(get_current_user)
):
    """Rerank documents based on query relevance."""
    return await optimizer.rerank(request.query, request.documents)

@router.post("/ingest")
async def trigger_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger background ingestion pipeline.
    This would typically schedule a job in the JobManager.
    """
    # For now, we stub the response as the pipeline requires a configured manager
    return {"status": "queued", "job_id": "job_123", "message": "Ingestion scheduled"}
