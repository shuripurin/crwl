"""
Create the results, labels, and agent_logs tables in the Ghost Postgres database.

Usage:
    python scripts/setup_db.py
    python scripts/setup_db.py --reset   # wipe all data
"""

import argparse
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true", help="Wipe all data from tables"
    )
    args = parser.parse_args()

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    if args.reset:
        cur.execute("TRUNCATE labels, agent_logs, results RESTART IDENTITY CASCADE")
        conn.commit()
        cur.close()
        conn.close()
        print("All data wiped.")
        return

    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id         SERIAL PRIMARY KEY,
            topic      TEXT,
            url        TEXT,
            title      TEXT,
            content    TEXT,
            agent_id   TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            labeled    BOOL DEFAULT FALSE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id         SERIAL PRIMARY KEY,
            result_id  INT REFERENCES results(id),
            labels     JSONB,
            agent_id   TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id         SERIAL PRIMARY KEY,
            agent_id   TEXT,
            agent_type TEXT,
            status     TEXT,
            message    TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully.")


if __name__ == "__main__":
    main()
