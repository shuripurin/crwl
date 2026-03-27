"""
Classify crawled results using parallel Claude agents and a user-defined schema.

Usage:
    python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3
"""

import argparse
import asyncio
import os

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


async def main():
    args = parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    asyncio.run(main())
