"""
Export crawled results and labels to JSON.

Usage:
    python scripts/export.py
    python scripts/export.py --topic "coral reef restoration"
    python scripts/export.py --output results.json
    python scripts/export.py --labeled-only
"""

import argparse
import json
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Export results and labels to JSON")
    parser.add_argument("--topic", help="Filter by topic")
    parser.add_argument(
        "--labeled-only", action="store_true", help="Only export labeled results"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="export.json",
        help="Output file path (default: export.json)",
    )
    args = parser.parse_args()

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT
            r.id, r.topic, r.url, r.title, r.content, r.agent_id, r.created_at,
            (SELECT l.labels FROM labels l WHERE l.result_id = r.id ORDER BY l.created_at DESC LIMIT 1) AS labels
        FROM results r
    """
    conditions = []
    params = []

    if args.topic:
        conditions.append("r.topic = %s")
        params.append(args.topic)
    if args.labeled_only:
        conditions.append("r.labeled = true")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY r.created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    # Convert datetime to string for JSON serialization
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()

    with open(args.output, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"Exported {len(rows)} results to {args.output}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
