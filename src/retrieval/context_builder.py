from collections import OrderedDict
from typing import Iterable


def _clean(value):
    if value is None:
        return ""

    value = str(value).strip()

    if value in {"", "___"}:
        return ""

    return value


def _event_key(result):
    """
    Create a lightweight deduplication key.

    We intentionally ignore event_id because multiple
    event rows can represent the same clinical information.
    """

    return (
        _clean(result.get("patient_id")),
        _clean(result.get("admission_id")),
        _clean(result.get("order_type")),
        _clean(result.get("drug")),
        _clean(result.get("test_name")),
        _clean(result.get("description")),
        _clean(result.get("comments")),
    )


def deduplicate_results(
    results: Iterable[dict],
    max_events: int = 8,
) -> list[dict]:
    """
    Remove near-duplicate retrieved events while
    preserving retrieval order.
    """

    unique = OrderedDict()

    for result in results:
        key = _event_key(result)

        if key not in unique:
            unique[key] = result

        if len(unique) >= max_events:
            break

    return list(unique.values())


def _is_medication_question(question: str) -> bool:
    """
    Identify questions that are primarily asking about
    medications.

    This is intentionally conservative. The purpose is not
    to classify the clinical question, but to prevent unrelated
    event metadata from being presented as medication evidence.
    """

    question = question.lower().strip()

    medication_terms = (
        "medication",
        "medications",
        "medicine",
        "medicines",
        "drug",
        "drugs",
        "prescribed",
        "prescription",
        "dose",
        "dosage",
        "drug therapy",
        "medication list",
    )

    return any(
        term in question
        for term in medication_terms
    )


def build_context(
    results: Iterable[dict],
    max_events: int = 8,
    question: str = "",
) -> str:
    """
    Convert retrieved database rows into structured
    context suitable for an LLM.

    For medication-focused questions, event type and care
    unit metadata are intentionally omitted from the context
    to prevent the LLM from incorrectly associating a
    medication with an admission, transfer, or care unit.
    """

    results = deduplicate_results(
        results,
        max_events=max_events,
    )

    if not results:
        return "No relevant clinical events were retrieved."

    medication_question = _is_medication_question(question)

    lines = []

    lines.append(
        "Retrieved clinical events:"
    )

    lines.append("")

    if medication_question:
        lines.append(
            "Context interpretation rule:"
        )
        lines.append(
            "- This is a medication-focused question."
        )
        lines.append(
            "- Use medication, dose, route, description, "
            "and comments as the primary evidence."
        )
        lines.append(
            "- Do not infer medication administration, "
            "receipt, use, or treatment from record metadata."
        )
        lines.append(
            "- Event type, care unit, admission, and transfer "
            "metadata are intentionally omitted because they "
            "do not by themselves establish a relationship "
            "with the medication."
        )
    else:
        lines.append(
            "Important interpretation note:"
        )
        lines.append(
            "- Event type, order type, and care unit are "
            "record metadata."
        )
        lines.append(
            "- These fields do not by themselves establish "
            "medication administration, treatment, or clinical action."
        )
        lines.append(
            "- Describe medications, tests, and other clinical "
            "items as documented in the retrieved record unless "
            "the record explicitly supports a specific action."
        )

    lines.append("")

    for index, result in enumerate(
        results,
        start=1,
    ):

        patient_id = _clean(
            result.get("patient_id")
        )

        admission_id = _clean(
            result.get("admission_id")
        )

        event_type = _clean(
            result.get("event_type")
        )

        order_type = _clean(
            result.get("order_type")
        )

        order_subtype = _clean(
            result.get("order_subtype")
        )

        drug = _clean(
            result.get("drug")
        )

        strength = _clean(
            result.get("prod_strength")
        )

        dose = _clean(
            result.get("dose_val_rx")
        )

        dose_unit = _clean(
            result.get("dose_unit_rx")
        )

        route = _clean(
            result.get("route")
        )

        careunit = _clean(
            result.get("careunit")
        )

        test_name = _clean(
            result.get("test_name")
        )

        organization = _clean(
            result.get("org_name")
        )

        comments = _clean(
            result.get("comments")
        )

        description = _clean(
            result.get("description")
        )

        lines.append(
            f"Event {index}:"
        )

        if patient_id:
            lines.append(
                f"- Patient ID: {patient_id}"
            )

        if admission_id:
            lines.append(
                f"- Admission ID: {admission_id}"
            )

        # Only expose event metadata for non-medication questions.
        if not medication_question:

            if event_type:
                lines.append(
                    f"- Event type (record metadata): {event_type}"
                )

            if order_type:
                lines.append(
                    f"- Order type (record metadata): {order_type}"
                )

            if order_subtype:
                lines.append(
                    f"- Order subtype (record metadata): {order_subtype}"
                )

        if drug:
            medication = drug

            if strength:
                medication += (
                    f" ({strength})"
                )

            lines.append(
                f"- Medication documented: {medication}"
            )

        if dose:
            dose_text = dose

            if dose_unit:
                dose_text += (
                    f" {dose_unit}"
                )

            lines.append(
                f"- Dose documented: {dose_text}"
            )

        if route:
            lines.append(
                f"- Route documented: {route}"
            )

        if not medication_question and careunit:
            lines.append(
                f"- Care unit (record metadata): {careunit}"
            )

        if test_name:
            lines.append(
                f"- Test documented: {test_name}"
            )

        if organization:
            lines.append(
                f"- Organization: {organization}"
            )

        if description:
            lines.append(
                f"- Clinical description: {description}"
            )

        if comments:
            lines.append(
                f"- Comments: {comments}"
            )

        lines.append("")

    return "\n".join(lines)


def build_patient_context(
    results: Iterable[dict],
    patient_id: int,
    question: str = "",
    max_events: int = 8,
) -> str:
    """
    Build context specifically for a requested patient.

    This performs an application-level safety check so
    unrelated patients are not accidentally passed to
    the LLM.
    """

    patient_results = [
        result
        for result in results
        if result.get("patient_id") == patient_id
    ]

    return build_context(
        patient_results,
        max_events=max_events,
        question=question,
    )
