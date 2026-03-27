"""
Spin up parallel Claude agents to web-search a topic and store findings.

Usage:
    python scripts/crawl.py --topic "coral reef restoration" --agents 3 --max-results 50
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


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


async def main():
    args = parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    asyncio.run(main())
