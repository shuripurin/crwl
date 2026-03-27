# web-research-labeler

Autonomous web research tool using parallel Claude agents with Ghost-hosted Postgres storage and a live Next.js dashboard.

## Overview

`web-research-labeler` crawls the web for a given topic, stores results in a Postgres database, labels results with configurable schemas, and displays live progress in a dashboard.

Languages: Python, TypeScript, CSS
Frameworks & Libraries: Next.js (dashboard UI), React (via Next.js)
Database: PostgreSQL — accessed via raw SQL using pg (Node.js) and psycopg2 (Python)
Cloud/Platform: Ghost CLI — used to provision and manage the Postgres database via DATABASE_URL
AI: Anthropic Claude API — parallel Claude agents using the web_search tool for crawling and labeling
APIs & Tools: Anthropic web search tool (web_search_20260209), REST API routes via Next.js
Other: Python venv, Shell scripting (start_dashboard.sh), .env config management 

## Repository Structure

- `scripts/`
  - `setup_db.py` — create Postgres tables
  - `crawl.py` — research web results using Claude agents
  - `label.py` — label unlabeled results using Claude agents
  - `start_dashboard.sh` — launch the dashboard
  - `requirements.txt` — Python dependencies
- `dashboard/`
  - `app/` — Next.js dashboard UI and API routes
  - `lib/db.ts` — shared database connection logic
  - `package.json` — dashboard dependencies and scripts
- `PLAN.md` — implementation plan and architecture notes
- `CLAUDE.md` — project-specific agent/research notes

## Setup

1. Install Ghost CLI and create a Ghost database:

```bash
curl -fsSL https://install.ghost.build | sh
ghost login
ghost create --name web-research
ghost connect <db-id>
```

2. Copy `.env.example` to `.env` and set:

```text
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://... # from ghost connect
```

3. Install Python dependencies and create the DB schema:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/setup_db.py
```

4. Install dashboard dependencies:

```bash
cd dashboard
npm install
```

## Usage

### Crawl a topic

```bash
python scripts/crawl.py --topic "coral reef restoration" --agents 3 --max-results 50
```

Each agent researches the topic from a different angle and inserts results into the `results` table.

### Start the dashboard

```bash
bash scripts/start_dashboard.sh
```

Then open `http://localhost:3000` to watch live stats, agent activity, and collected results.

### Label results

```bash
python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3
```

This command classifies unlabeled results and stores structured labels in the `labels` table.

## Architecture

### Python Scripts

- `crawl.py`
  - Uses parallel Claude agents with the `web_search_20260209` tool
  - Stores extracted `{url, title, content}` results in Postgres
  - Logs agent progress and errors in `agent_logs`
  - Uses isolated DB connections per agent for safe concurrency

- `label.py`
  - Fetches unlabeled results via `FOR UPDATE SKIP LOCKED`
  - Prompts Claude to classify results against a schema
  - Records labels and marks results as labeled

### Dashboard

- `dashboard/app/page.tsx` polls API endpoints for live updates
- `dashboard/app/api/stats/route.ts` summarizes counts and recent logs
- `dashboard/app/api/results/route.ts` returns the latest results and labels
- `dashboard/lib/db.ts` provides a shared `pg.Pool` using `DATABASE_URL`

## Verification

1. Confirm tables exist with:
   - `python scripts/setup_db.py`
   - `ghost psql <db-id>`
2. Run crawl:
   - `python scripts/crawl.py --topic "coral reef restoration" --agents 2 --max-results 10`
3. Launch the dashboard:
   - `bash scripts/start_dashboard.sh`
4. Label results:
   - `python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 2`
