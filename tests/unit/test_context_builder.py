from src.retrieval.context_builder import (
    build_context,
    build_patient_context,
)


def sample_result(**overrides):
    result = {
        "patient_id": 7,
        "admission_id": 11,
        "event_type": "transfer",
        "order_type": "Medications",
        "order_subtype": "Medication",
        "drug": "QUEtiapine Fumarate",
        "prod_strength": "1mg Vial",
        "dose_val_rx": "1",
        "dose_unit_rx": "mg",
        "route": "IM",
        "careunit": "Neurology",
        "test_name": "",
        "org_name": "",
        "description": "Medication record",
        "comments": "Medication documented",
    }

    result.update(overrides)
    return result


def test_medication_context_hides_event_metadata():
    results = [
        sample_result(),
    ]

    context = build_context(
        results,
        max_events=8,
        question="What medications were documented?",
    )

    assert "Medication documented: QUEtiapine Fumarate (1mg Vial)" in context
    assert "Dose documented: 1 mg" in context
    assert "Route documented: IM" in context

    assert "- Event type (record metadata):" not in context
    assert "- Order type (record metadata):" not in context
    assert "- Order subtype (record metadata):" not in context
    assert "- Care unit (record metadata):" not in context
    assert "Neurology" not in context


def test_general_context_keeps_event_metadata():
    results = [
        sample_result(),
    ]

    context = build_context(
        results,
        max_events=8,
        question="What events occurred?",
    )

    assert "Event type (record metadata): transfer" in context
    assert "Order type (record metadata): Medications" in context
    assert "Order subtype (record metadata): Medication" in context
    assert "Care unit (record metadata): Neurology" in context


def test_patient_context_filters_other_patients():
    results = [
        sample_result(patient_id=7),
        sample_result(
            patient_id=8,
            admission_id=20,
            drug="Aspirin",
        ),
    ]

    context = build_patient_context(
        results,
        patient_id=7,
        question="What medications were documented?",
        max_events=8,
    )

    assert "QUEtiapine Fumarate" in context
    assert "Aspirin" not in context
    assert "Patient ID: 8" not in context


def test_empty_context():
    context = build_context(
        [],
        max_events=8,
        question="What medications were documented?",
    )

    assert context == "No relevant clinical events were retrieved."


def test_deduplication():
    results = [
        sample_result(),
        sample_result(),
        sample_result(
            drug="Captopril",
            prod_strength="17g Packet",
            dose_val_rx="17",
            dose_unit_rx="g",
            route="PO/NG",
        ),
    ]

    context = build_context(
        results,
        max_events=8,
        question="What medications were documented?",
    )

    assert context.count("QUEtiapine Fumarate") == 1
    assert context.count("Captopril") == 1
