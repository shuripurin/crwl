"""
Spin up parallel Claude agents to web-search a topic and store findings.

Usage:
    python scripts/crawl.py --topic "coral reef restoration" --agents 3 --max-results 50
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

ANGLES = [
    "recent news and current events",
    "academic research and scientific studies",
    "practical applications and real-world use cases",
    "datasets and statistics",
    "case studies and success stories",
    "tutorials and how-to guides",
    "opinion and expert commentary",
    "historical context and background",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crawl a topic with parallel Claude agents"
    )
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument(
        "--agents", type=int, default=3, help="Number of parallel agents"
    )
    parser.add_argument(
        "--max-results", type=int, default=50, help="Max results to collect"
    )
    return parser.parse_args()


def db_log(conn, agent_id: str, status: str, message: str):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO agent_logs (agent_id, agent_type, status, message) VALUES (%s, %s, %s, %s)",
            (agent_id, "crawler", status, message),
        )
    conn.commit()


def db_insert_result(
    conn, agent_id: str, topic: str, url: str, title: str, content: str
):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO results (topic, url, title, content, agent_id) VALUES (%s, %s, %s, %s, %s)",
            (topic, url, title, content, agent_id),
        )
    conn.commit()


def extract_json_blocks(text: str) -> tuple[list[dict], list[str]]:
    blocks = []
    warnings = []
    for match in re.finditer(r"\{[^{}]*\}", text, re.DOTALL):
        try:
            obj = json.loads(match.group())
            if all(k in obj for k in ("url", "title", "content")):
                blocks.append(obj)
        except json.JSONDecodeError:
            warnings.append(f"Failed to parse JSON block: {match.group()[:80]}")
    return blocks, warnings


async def run_agent(
    agent_id: str, topic: str, angle: str, max_results: int, db_url: str
):
    conn = await asyncio.to_thread(psycopg2.connect, db_url)
    client = anthropic.AsyncAnthropic()

    system = (
        f"You are a research agent focused on: {angle}.\n"
        f"Research the topic '{topic}' from that angle using web search.\n"
        "For each relevant result you find, output a JSON block on its own line:\n"
        '{"url": "...", "title": "...", "content": "brief summary"}\n'
        "Aim to find as many distinct, high-quality results as possible."
    )

    messages = [
        {
            "role": "user",
            "content": f"Research '{topic}' focusing on {angle}. Output JSON blocks for each result.",
        }
    ]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 10}]

    await asyncio.to_thread(
        db_log, conn, agent_id, "running", f"Researching '{topic}' from angle: {angle}"
    )

    results_found = 0
    turn = 0
    max_turns = 20

    try:
        while turn < max_turns and results_found < max_results:
            attempt = 0
            response = None
            while attempt < 3:
                try:
                    response = await client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=4096,
                        system=system,
                        tools=tools,
                        messages=messages,
                    )
                    break
                except anthropic.RateLimitError:
                    wait = 2**attempt
                    await asyncio.to_thread(
                        db_log,
                        conn,
                        agent_id,
                        "warning",
                        f"Rate limited, retrying in {wait}s",
                    )
                    await asyncio.sleep(wait)
                    attempt += 1

            if response is None:
                await asyncio.to_thread(
                    db_log,
                    conn,
                    agent_id,
                    "error",
                    "Max retries exceeded on rate limit",
                )
                break

            for block in response.content:
                if block.type == "text":
                    extracted, parse_warnings = extract_json_blocks(block.text)
                    for warn in parse_warnings:
                        await asyncio.to_thread(db_log, conn, agent_id, "warning", warn)
                    for item in extracted:
                        if results_found >= max_results:
                            break
                        try:
                            await asyncio.to_thread(
                                db_insert_result,
                                conn,
                                agent_id,
                                topic,
                                item["url"],
                                item["title"],
                                item["content"],
                            )
                            results_found += 1
                        except Exception as e:
                            await asyncio.to_thread(
                                db_log,
                                conn,
                                agent_id,
                                "warning",
                                f"Failed to insert result: {e}",
                            )

            if response.stop_reason == "end_turn":
                break

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Continue searching."})
            turn += 1

        await asyncio.to_thread(
            db_log, conn, agent_id, "completed", f"Found {results_found} results"
        )

    except Exception as e:
        await asyncio.to_thread(db_log, conn, agent_id, "error", str(e))
    finally:
        conn.close()


async def main():
    args = parse_args()
    db_url = os.environ["DATABASE_URL"]

    agents = []
    for i in range(args.agents):
        agent_id = f"crawler-{uuid.uuid4().hex[:8]}"
        angle = ANGLES[i % len(ANGLES)]
        agents.append(
            run_agent(
                agent_id,
                args.topic,
                angle,
                args.max_results // args.agents or 1,
                db_url,
            )
        )

    await asyncio.gather(*agents)
    print("All crawl agents finished.")


if __name__ == "__main__":
    asyncio.run(main())
