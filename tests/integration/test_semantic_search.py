from src.retrieval.semantic_search import semantic_search


def test_patient_and_admission_scoped_retrieval():
    results = semantic_search(
        query="What medications were documented?",
        top_k=10,
        patient_id=7,
        admission_id=11,
    )

    assert results
    assert len(results) <= 10

    for result in results:
        assert result["patient_id"] == 7
        assert result["admission_id"] == 11
