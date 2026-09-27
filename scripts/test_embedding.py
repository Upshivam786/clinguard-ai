import os
import sys

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "qwen/qwen3-embedding-8b",
)


if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY is not configured.")
    sys.exit(1)


client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


def get_database_url():
    db = os.getenv("POSTGRES_DB", "clinguard")
    user = os.getenv("POSTGRES_USER", "clinguard_app")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")

    if not password:
        raise RuntimeError("POSTGRES_PASSWORD is not configured.")

    return (
        f"postgresql://{user}:{password}"
        f"@{host}:{port}/{db}"
    )


def main():
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT event_id, embedding_text
                FROM clinical.clinical_events
                WHERE embedding IS NULL
                  AND embedding_text IS NOT NULL
                  AND embedding_text <> ''
                ORDER BY event_id
                LIMIT 5;
                """
            )

            rows = cur.fetchall()

    if not rows:
        print("No events found for embedding.")
        return

    print(f"Testing embeddings for {len(rows)} events...")
    print(f"Model: {EMBEDDING_MODEL}")

    texts = [row[1] for row in rows]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    print(f"Returned embeddings: {len(response.data)}")

    for row, embedding_data in zip(rows, response.data):
        vector = embedding_data.embedding

        print(
            f"event_id={row[0]} "
            f"dimension={len(vector)} "
            f"first_3={vector[:3]}"
        )


if __name__ == "__main__":
    main()
