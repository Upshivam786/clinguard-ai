from typing import Optional

from src.retrieval.semantic_search import semantic_search
from src.retrieval.context_builder import build_patient_context
from src.llm.generator import generate_answer
from src.guardrails.response_guard import sanitize_clinical_answer


class RAGService:
    """
    Orchestrates patient-scoped clinical retrieval and
    grounded LLM generation.

    Patient and admission identifiers are explicit application
    parameters. They are never inferred by the LLM.
    """

    def query(
        self,
        question: str,
        patient_id: int,
        admission_id: Optional[int] = None,
        top_k: int = 100,
        max_context_events: int = 8,
    ) -> dict:

        # ---------------------------------------------------------
        # 1. Validate request
        # ---------------------------------------------------------
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if patient_id < 1:
            raise ValueError(
                "patient_id must be a positive integer."
            )

        if admission_id is not None and admission_id < 1:
            raise ValueError(
                "admission_id must be a positive integer."
            )

        # ---------------------------------------------------------
        # 2. Patient/admission-scoped semantic retrieval
        # ---------------------------------------------------------
        results = semantic_search(
            query=question,
            top_k=top_k,
            patient_id=patient_id,
            admission_id=admission_id,
        )

        # ---------------------------------------------------------
        # 3. Application-level patient/admission boundary
        # ---------------------------------------------------------
        for result in results:

            if result.get("patient_id") != patient_id:
                raise RuntimeError(
                    "Patient boundary violation detected."
                )

            if (
                admission_id is not None
                and result.get("admission_id") != admission_id
            ):
                raise RuntimeError(
                    "Admission boundary violation detected."
                )

        # ---------------------------------------------------------
        # 4. Build grounded LLM context
        # ---------------------------------------------------------
        context = build_patient_context(
            results,
            patient_id=patient_id,
            question=question,
            max_events=max_context_events,
        )

        # ---------------------------------------------------------
        # 5. Generate grounded answer
        # ---------------------------------------------------------
        if not results:
            answer = (
                "No relevant clinical events were retrieved "
                "for the requested patient scope."
            )

        else:
            answer = generate_answer(
                query=question,
                context=context,
            )

            # Deterministic application-level wording guardrail.
            answer = sanitize_clinical_answer(answer)

        # ---------------------------------------------------------
        # 6. Return structured response
        # ---------------------------------------------------------
        return {
            "question": question,
            "patient_id": patient_id,
            "admission_id": admission_id,
            "retrieved_count": len(results),
            "context_event_count": min(
                len(results),
                max_context_events,
            ),
            "answer": answer,
            "results": results,
        }
