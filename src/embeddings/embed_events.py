import os
import sys
import time

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

BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))
MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "5"))


def database_url():
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


def create_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def fetch_batch(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_id, embedding_text
            FROM clinical.clinical_events
            WHERE embedding IS NULL
              AND embedding_text IS NOT NULL
              AND embedding_text <> ''
            ORDER BY event_id
            LIMIT %s
            """,
            (BATCH_SIZE,),
        )

        return cur.fetchall()


def generate_embeddings(client, texts):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )

            vectors = [item.embedding for item in response.data]

            if len(vectors) != len(texts):
                raise RuntimeError(
                    f"Expected {len(texts)} embeddings, "
                    f"received {len(vectors)}"
                )

            return vectors

        except Exception as exc:
            last_error = exc

            wait_seconds = min(2 ** attempt, 30)

            print(
                f"Embedding request failed "
                f"(attempt {attempt}/{MAX_RETRIES}): {exc}"
            )

            if attempt < MAX_RETRIES:
                print(f"Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)

    raise RuntimeError(
        f"Embedding failed after {MAX_RETRIES} attempts"
    ) from last_error


def save_embeddings(conn, rows, vectors):
    with conn.cursor() as cur:
        for (event_id, _), vector in zip(rows, vectors):
            cur.execute(
                """
                UPDATE clinical.clinical_events
                SET embedding = %s
                WHERE event_id = %s
                """,
                (vector, event_id),
            )

    conn.commit()


def main():
    print("ClinGuard AI embedding worker")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Batch size: {BATCH_SIZE}")

    client = create_client()

    with psycopg.connect(database_url()) as conn:

        total_processed = 0

        while True:
            rows = fetch_batch(conn)

            if not rows:
                print("No remaining events to embed.")
                break

            print(
                f"Processing events "
                f"{rows[0][0]} → {rows[-1][0]} "
                f"({len(rows)} records)"
            )

            texts = [row[1] for row in rows]

            vectors = generate_embeddings(
                client,
                texts,
            )

            # Safety check before writing.
            for vector in vectors:
                if len(vector) != 4096:
                    raise RuntimeError(
                        f"Unexpected embedding dimension: "
                        f"{len(vector)}"
                    )

            save_embeddings(
                conn,
                rows,
                vectors,
            )

            total_processed += len(rows)

            print(
                f"Saved batch. "
                f"Session total: {total_processed}"
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(130)
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
