import pytest

from src.rag.service import RAGService


def test_rejects_wrong_patient(monkeypatch):
    service = RAGService()

    results = [
        {
            "patient_id": 8,
            "admission_id": 20,
            "drug": "Aspirin",
        }
    ]

    monkeypatch.setattr(
        "src.rag.service.semantic_search",
        lambda **kwargs: results,
    )

    with pytest.raises(
        RuntimeError,
        match="Patient boundary violation detected",
    ):
        service.query(
            question="What medications were documented?",
            patient_id=7,
            admission_id=11,
        )


def test_rejects_wrong_admission(monkeypatch):
    service = RAGService()

    results = [
        {
            "patient_id": 7,
            "admission_id": 20,
            "drug": "Aspirin",
        }
    ]

    monkeypatch.setattr(
        "src.rag.service.semantic_search",
        lambda **kwargs: results,
    )

    with pytest.raises(
        RuntimeError,
        match="Admission boundary violation detected",
    ):
        service.query(
            question="What medications were documented?",
            patient_id=7,
            admission_id=11,
        )


def test_rejects_invalid_patient_id():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="patient_id must be a positive integer",
    ):
        service.query(
            question="What medications were documented?",
            patient_id=0,
        )


def test_rejects_invalid_admission_id():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="admission_id must be a positive integer",
    ):
        service.query(
            question="What medications were documented?",
            patient_id=7,
            admission_id=0,
        )


def test_rejects_empty_question():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        service.query(
            question="   ",
            patient_id=7,
        )


def test_returns_safe_empty_retrieval(monkeypatch):
    service = RAGService()

    monkeypatch.setattr(
        "src.rag.service.semantic_search",
        lambda **kwargs: [],
    )

    result = service.query(
        question="What medications were documented?",
        patient_id=7,
        admission_id=11,
    )

    assert result["retrieved_count"] == 0
    assert result["context_event_count"] == 0
    assert "No relevant clinical events were retrieved" in result["answer"]
