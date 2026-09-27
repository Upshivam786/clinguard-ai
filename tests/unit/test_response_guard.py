from src.guardrails.response_guard import sanitize_clinical_answer


def test_removes_medication_administration_claims():
    answer = (
        "The medication was administered to the patient "
        "and was given during admission."
    )

    sanitized = sanitize_clinical_answer(answer)

    assert "administered" not in sanitized.lower()
    assert "was given" not in sanitized.lower()
    assert "was documented" in sanitized.lower()


def test_removes_unsupported_completeness_sentence():
    answer = (
        "The retrieved records document two medications. "
        "No other medications are explicitly documented."
    )

    sanitized = sanitize_clinical_answer(answer)

    assert "no other" not in sanitized.lower()
    assert "two medications" in sanitized.lower()


def test_removes_nothing_else_claim():
    answer = (
        "The retrieved records document Captopril. "
        "Nothing else was documented."
    )

    sanitized = sanitize_clinical_answer(answer)

    assert "nothing else" not in sanitized.lower()
    assert "Captopril" in sanitized


def test_preserves_safe_grounded_answer():
    answer = (
        "The retrieved records document Captopril. "
        "Dose: 17 g. Route: PO/NG."
    )

    sanitized = sanitize_clinical_answer(answer)

    assert sanitized == answer


def test_empty_answer():
    assert sanitize_clinical_answer("") == ""
    assert sanitize_clinical_answer(None) is None

