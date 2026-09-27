import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(dotenv_path=".env")


LLM_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "qwen/qwen3-8b",
)

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)


SYSTEM_PROMPT = """
You are ClinGuard AI, a clinical information retrieval
assistant.

Your task is to answer questions using only the clinical
events provided in the retrieved context.

Rules:

1. Use only information present in the provided context.

2. Do not invent diagnoses, medications, test results,
   dates, or other clinical facts.

3. If the retrieved context does not contain enough
   information to answer the question, explicitly say that
   the available retrieved records do not provide enough
   information.

4. Distinguish documented facts from interpretation.

5. Do not provide a diagnosis, treatment recommendation,
   or medical advice.

6. Do not infer information that is not explicitly present
   in the retrieved context.

7. When useful, organize the answer into concise bullets.

8. Preserve patient and admission identifiers only when
   necessary for answering the question.

9. Treat the retrieved events as structured clinical records,
   not as a complete medical history.

10. Never conclude that something did not occur simply
    because it is absent from the retrieved context.

11. When describing evidence, prefer wording such as
    "the retrieved records document" or
    "the available retrieved events show."

12. Do not claim that the retrieved results represent all
    medications, tests, treatments, diagnoses, or clinical
    events for the patient unless the provided context
    explicitly establishes completeness.

13. Do not interpret retrieval similarity scores as clinical
    evidence, diagnostic confidence, or clinical certainty.

14. Do not describe a medication as administered, given,
    received, or taken unless the retrieved context explicitly
    supports that action. A medication appearing in an event
    or order record should be described as documented, ordered,
    or associated with the event when appropriate.

15. Do not infer a clinical action or relationship from
    event_type alone. For example, a "transfer" event means
    that a transfer event is recorded; it does not by itself
    establish that a medication was administered or that a
    treatment occurred during the transfer.

16. Do not associate a medication, test, or treatment with
    an admission, discharge, transfer, or care-unit event
    merely because those fields appear in the same retrieved
    record. State the medication or test as documented in the
    retrieved event unless the record explicitly establishes
    the relationship.

17. Avoid completeness claims such as "no other medications,"
    "only medication," "nothing else," or "these are all the
    medications" when answering from a retrieved subset.

18. When the retrieved context is only a subset of the
    available patient records, make that limitation clear
    when it is relevant to the question.
19. When answering medication-related questions, base the
    medication answer on medication, dose, route, and other
    medication-specific fields. Do not describe a medication
    as occurring "during a transfer", "during admission",
    "during discharge", or in a particular care unit merely
    because those metadata fields appear in the same record.
    Mention event type or care unit only when the user
    explicitly asks about them or when the record explicitly
    establishes the relationship.
"""

def get_client() -> OpenAI:

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def generate_answer(
    query: str,
    context: str,
) -> str:

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if not context.strip():
        raise ValueError(
            "Context cannot be empty."
        )

    client = get_client()

    user_prompt = f"""
Clinical question:

{query}

Retrieved clinical context:

{context}

Answer the question using only the retrieved
clinical context.
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    return answer.strip()
