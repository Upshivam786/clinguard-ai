from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from src.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from src.rag.service import RAGService


app = FastAPI(
    title="ClinGuard AI",
    description=(
        "Privacy-first clinical information retrieval API "
        "using PostgreSQL, pgvector, and grounded LLM generation."
    ),
    version="0.2.0",
)

rag_service = RAGService()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserResponse(BaseModel):
    username: str
    role: str


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


@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(
        form_data.username,
        form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        username=user["username"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
    )


@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def me(
    current_user: dict = Depends(get_current_user),
):
    return UserResponse(
        username=current_user["username"],
        role=current_user["role"],
    )


@app.post(
    "/query",
    response_model=QueryResponse,
)
def query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
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
