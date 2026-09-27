from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.rag.service import RAGService


app = FastAPI(
    title="ClinGuard AI",
    description=(
        "Privacy-first clinical information retrieval API "
        "using PostgreSQL, pgvector, and grounded LLM generation."
    ),
    version="0.1.0",
)

rag_service = RAGService()


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language clinical information query.",
    )

    patient_id: int = Field(
        ...,
        ge=1,
        description="Explicit patient identifier.",
    )

    admission_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional admission identifier.",
    )

    top_k: int = Field(
        default=100,
        ge=1,
        le=200,
        description="Number of semantic retrieval candidates.",
    )

    max_context_events: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum events passed to the LLM.",
    )


class QueryResponse(BaseModel):
    question: str
    patient_id: int
    admission_id: Optional[int]
    retrieved_count: int
    context_event_count: int
    answer: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "clinguard-ai",
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):

    try:
        result = rag_service.query(
            question=request.question,
            patient_id=request.patient_id,
            admission_id=request.admission_id,
            top_k=request.top_k,
            max_context_events=request.max_context_events,
        )

        return QueryResponse(
            question=result["question"],
            patient_id=result["patient_id"],
            admission_id=result["admission_id"],
            retrieved_count=result["retrieved_count"],
            context_event_count=result["context_event_count"],
            answer=result["answer"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Clinical query processing failed.",
        ) from exc
