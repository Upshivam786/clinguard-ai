import os
from typing import Optional

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(dotenv_path=".env")


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "qwen/qwen3-embedding-8b",
)

EMBEDDING_DIMENSION = 2000

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)


def get_database_url() -> str:
    return (
        f"postgresql://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.getenv('POSTGRES_HOST', '127.0.0.1')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )


def get_embedding_client() -> OpenAI:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def embed_query(query: str) -> list[float]:
    """
    Generate a 2000-dimensional embedding
    for a user query.
    """

    client = get_embedding_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
        dimensions=EMBEDDING_DIMENSION,
    )

    vector = response.data[0].embedding

    if len(vector) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"received {len(vector)}"
        )

    return vector


def semantic_search(
    query: str,
    top_k: int = 10,
    patient_id: Optional[int] = None,
    admission_id: Optional[int] = None,
    min_similarity: Optional[float] = None,
) -> list[dict]:

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if top_k < 1 or top_k > 100:
        raise ValueError(
            "top_k must be between 1 and 100."
        )

    query_vector = embed_query(query)

    filters = [
        "embedding_2000 IS NOT NULL"
    ]

    params = []

    if patient_id is not None:
        filters.append(
            "patient_id = %s"
        )
        params.append(patient_id)

    if admission_id is not None:
        filters.append(
            "admission_id = %s"
        )
        params.append(admission_id)

    where_clause = " AND ".join(filters)

    sql = f"""
        SELECT
            event_id,
            patient_id,
            admission_id,
            event_type,
            order_type,
            order_subtype,
            transaction_type,
            drug,
            formulary_drug_cd,
            prod_strength,
            dose_val_rx,
            dose_unit_rx,
            form_unit_disp,
            route,
            careunit,
            spec_type_desc,
            test_name,
            org_name,
            ab_name,
            comments,
            drg_type,
            description,
            drg_severity,
            drg_mortality,
            1 - (
                embedding_2000 <=> %s::vector
            ) AS similarity
        FROM clinical.clinical_events
        WHERE {where_clause}
        ORDER BY embedding_2000 <=> %s::vector
        LIMIT %s;
    """

    params_with_vector = (
        [query_vector]
        + params
        + [query_vector, top_k]
    )

    with psycopg.connect(
        get_database_url()
    ) as conn:

        with conn.cursor() as cur:

            # pgvector filtered HNSW search:
            # iterative scanning allows PostgreSQL to continue
            # searching after approximate candidates are removed
            # by patient/admission filters.
            cur.execute(
                "SET hnsw.iterative_scan = strict;"
            )
            cur.execute(
                "SET hnsw.ef_search = 1000;"
            )

            cur.execute(
                sql,
                params_with_vector,
            )

            rows = cur.fetchall()

            columns = [
                description[0]
                for description in cur.description
            ]

    results = [
        dict(zip(columns, row))
        for row in rows
    ]

    if min_similarity is not None:
        results = [
            result
            for result in results
            if result["similarity"]
            >= min_similarity
        ]

    return results
