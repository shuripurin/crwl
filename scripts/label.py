"""
Classify crawled results using parallel Claude agents and a user-defined schema.

Usage:
    python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3
"""

import argparse
import asyncio
import json
import os
import re
import uuid

import anthropic
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Label results with parallel Claude agents"
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Labeling schema (e.g. 'relevance:high/medium/low, type:article/study/news')",
    )
    parser.add_argument(
        "--agents", type=int, default=3, help="Number of parallel agents"
    )
    parser.add_argument(
        "--batch-size", type=int, default=5, help="Rows per agent per batch"
    )
    return parser.parse_args()


def parse_schema(schema_str: str) -> dict[str, list[str]]:
    """Parse 'relevance:high/medium/low, type:article/study' into {field: [values]}."""
    result = {}
    for part in schema_str.split(","):
        part = part.strip()
        if ":" in part:
            field, values = part.split(":", 1)
            result[field.strip()] = [v.strip() for v in values.split("/")]
    return result


def validate_labels(labels: dict, schema: dict[str, list[str]]) -> bool:
    for field, allowed in schema.items():
        if field not in labels:
            return False
        if labels[field] not in allowed:
            return False
    return True


def db_log(conn, agent_id: str, status: str, message: str):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO agent_logs (agent_id, agent_type, status, message) VALUES (%s, %s, %s, %s)",
            (agent_id, "labeler", status, message),
        )
    conn.commit()


def db_claim_batch(conn, batch_size: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, content
            FROM results
            WHERE labeled = FALSE
            FOR UPDATE SKIP LOCKED
            LIMIT %s
            """,
            (batch_size,),
        )
        rows = cur.fetchall()
    conn.commit()
    return [{"id": r[0], "title": r[1], "content": r[2]} for r in rows]


def db_save_labels(conn, result_id: int, labels: dict, agent_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO labels (result_id, labels, agent_id) VALUES (%s, %s, %s)",
            (result_id, json.dumps(labels), agent_id),
        )
        cur.execute("UPDATE results SET labeled = TRUE WHERE id = %s", (result_id,))
    conn.commit()


async def run_agent(agent_id: str, schema_str: str, batch_size: int, db_url: str):
    conn = psycopg2.connect(db_url)
    client = anthropic.AsyncAnthropic()
    schema = parse_schema(schema_str)

    db_log(conn, agent_id, "running", f"Labeling with schema: {schema_str}")

    labeled_count = 0

    try:
        while True:
            batch = await asyncio.to_thread(db_claim_batch, conn, batch_size)
            if not batch:
                break

            items_text = "\n\n".join(
                f"ID: {item['id']}\nTitle: {item['title']}\nContent: {item['content']}"
                for item in batch
            )

            prompt = (
                f"Classify each result using this schema: {schema_str}\n\n"
                f"For each result, return a JSON object on its own line with 'id' and one key per schema field.\n"
                f'Example: {{"id": 1, "relevance": "high", "type": "article"}}\n\n'
                f"Results to classify:\n{items_text}"
            )

            attempt = 0
            response = None
            while attempt < 3:
                try:
                    response = await client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    break
                except anthropic.RateLimitError:
                    wait = 2**attempt
                    db_log(
                        conn, agent_id, "warning", f"Rate limited, retrying in {wait}s"
                    )
                    await asyncio.sleep(wait)
                    attempt += 1

            if response is None:
                db_log(conn, agent_id, "error", "Max retries exceeded on rate limit")
                break

            text = next((b.text for b in response.content if b.type == "text"), "")

            for match in re.finditer(r"\{[^{}]*\}", text, re.DOTALL):
                try:
                    obj = json.loads(match.group())
                    result_id = obj.pop("id", None)
                    if result_id is None:
                        continue
                    if not validate_labels(obj, schema):
                        db_log(
                            conn,
                            agent_id,
                            "warning",
                            f"Labels don't match schema for id {result_id}, skipping",
                        )
                        continue
                    await asyncio.to_thread(
                        db_save_labels, conn, result_id, obj, agent_id
                    )
                    labeled_count += 1
                except (json.JSONDecodeError, Exception) as e:
                    db_log(conn, agent_id, "warning", f"Failed to save label: {e}")

        db_log(conn, agent_id, "completed", f"Labeled {labeled_count} results")

    except Exception as e:
        db_log(conn, agent_id, "error", str(e))
    finally:
        conn.close()


async def main():
    args = parse_args()
    db_url = os.environ["DATABASE_URL"]

    agents = [
        run_agent(
            f"labeler-{uuid.uuid4().hex[:8]}",
            args.schema,
            args.batch_size,
            db_url,
        )
        for _ in range(args.agents)
    ]

    await asyncio.gather(*agents)
    print("All label agents finished.")


if __name__ == "__main__":
    asyncio.run(main())
