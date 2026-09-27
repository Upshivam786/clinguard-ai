import argparse
import os
import sys
import time

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

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def get_database_url():
    required = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    missing = [
        name
        for name in required
        if not os.getenv(name)
    ]

    if missing:
        raise RuntimeError(
            f"Missing database environment variables: {missing}"
        )

    return (
        f"postgresql://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.getenv('POSTGRES_HOST', '127.0.0.1')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )


def create_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def fetch_batch(
    conn,
    start_id,
    end_id,
    batch_size,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                event_id,
                embedding_text
            FROM clinical.clinical_events
            WHERE event_id BETWEEN %s AND %s
              AND embedding_2000 IS NULL
              AND embedding_text IS NOT NULL
              AND embedding_text <> ''
            ORDER BY event_id
            LIMIT %s;
            """,
            (
                start_id,
                end_id,
                batch_size,
            ),
        )

        return cur.fetchall()


def generate_embeddings(
    client,
    texts,
    max_retries=5,
):
    last_error = None

    for attempt in range(
        1,
        max_retries + 1,
    ):
        try:

            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
                dimensions=EMBEDDING_DIMENSION,
            )

            vectors = [
                item.embedding
                for item in response.data
            ]

            if len(vectors) != len(texts):
                raise RuntimeError(
                    f"Expected {len(texts)} embeddings, "
                    f"received {len(vectors)}"
                )

            for vector in vectors:

                if len(vector) != EMBEDDING_DIMENSION:
                    raise RuntimeError(
                        f"Expected dimension "
                        f"{EMBEDDING_DIMENSION}, "
                        f"received {len(vector)}"
                    )

            return vectors

        except Exception as exc:

            last_error = exc

            print(
                f"API error "
                f"(attempt {attempt}/{max_retries}): "
                f"{exc}",
                flush=True,
            )

            if attempt < max_retries:

                sleep_seconds = min(
                    2 ** attempt,
                    30,
                )

                print(
                    f"Retrying in {sleep_seconds}s...",
                    flush=True,
                )

                time.sleep(
                    sleep_seconds,
                )

    raise RuntimeError(
        "Embedding request failed after "
        f"{max_retries} attempts"
    ) from last_error


def save_batch(
    conn,
    rows,
    vectors,
):
    with conn.cursor() as cur:

        for (event_id, _), vector in zip(
            rows,
            vectors,
        ):

            cur.execute(
                """
                UPDATE clinical.clinical_events
                SET embedding_2000 = %s
                WHERE event_id = %s;
                """,
                (
                    vector,
                    event_id,
                ),
            )

    conn.commit()


def worker(
    start_id,
    end_id,
    batch_size,
):
    print("=" * 60)
    print("ClinGuard AI 2000-D Embedding Worker")
    print(f"Range: {start_id} → {end_id}")
    print(f"Batch size: {batch_size}")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dimension: {EMBEDDING_DIMENSION}")
    print("=" * 60)

    client = create_client()

    total_processed = 0
    start_time = time.time()

    with psycopg.connect(
        get_database_url()
    ) as conn:

        while True:

            rows = fetch_batch(
                conn,
                start_id,
                end_id,
                batch_size,
            )

            if not rows:
                break

            event_start = rows[0][0]
            event_end = rows[-1][0]

            texts = [
                row[1]
                for row in rows
            ]

            print(
                f"Embedding events "
                f"{event_start} → {event_end} "
                f"({len(rows)} records)...",
                flush=True,
            )

            vectors = generate_embeddings(
                client,
                texts,
            )

            save_batch(
                conn,
                rows,
                vectors,
            )

            total_processed += len(rows)

            elapsed = (
                time.time() -
                start_time
            )

            rate = (
                total_processed /
                elapsed
                if elapsed > 0
                else 0
            )

            print(
                f"Saved batch | "
                f"worker_total="
                f"{total_processed} | "
                f"rate="
                f"{rate:.2f} records/sec",
                flush=True,
            )

    elapsed = (
        time.time() -
        start_time
    )

    print("=" * 60)
    print(
        f"WORKER COMPLETE | "
        f"range={start_id}-{end_id} | "
        f"processed={total_processed} | "
        f"time={elapsed / 60:.2f} min"
    )
    print("=" * 60)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--end",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    try:

        worker(
            args.start,
            args.end,
            args.batch_size,
        )

    except KeyboardInterrupt:

        print(
            "\nWorker stopped by user."
        )

        sys.exit(130)

    except Exception as exc:

        print(
            f"\nWORKER ERROR: {exc}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
