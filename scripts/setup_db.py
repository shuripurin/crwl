"""
Create the results, labels, and agent_logs tables in the Ghost Postgres database.

Usage:
    python scripts/setup_db.py
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    db_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id          SERIAL PRIMARY KEY,
            topic       TEXT,
            url         TEXT,
            title       TEXT,
            content     TEXT,
            agent_id    TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW(),
            labeled     BOOL DEFAULT FALSE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id          SERIAL PRIMARY KEY,
            result_id   INT REFERENCES results(id),
            labels      JSONB,
            agent_id    TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id          SERIAL PRIMARY KEY,
            agent_id    TEXT,
            agent_type  TEXT,
            status      TEXT,
            message     TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.close()
    conn.close()
    print("Tables created (or already exist).")


if __name__ == "__main__":
    main()
