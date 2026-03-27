# Implementation Plan: web-research-labeler

## Context

Building a full-stack autonomous research tool from scratch. The system spins up parallel Claude agents to web-search a topic, stores findings in Ghost (Postgres), labels them via a configurable schema, and displays live progress in a Next.js dashboard.

## Directory Structure

```
crwl/
├── PLAN.md
├── CLAUDE.md
├── .env.example
├── scripts/
│   ├── requirements.txt
│   ├── setup_db.py
│   ├── crawl.py
│   ├── label.py
│   └── start_dashboard.sh
└── dashboard/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.ts
    ├── .env.example
    ├── lib/
    │   └── db.ts
    └── app/
        ├── layout.tsx
        ├── page.tsx
        ├── globals.css
        └── api/
            ├── stats/route.ts
            └── results/route.ts
```

## Phase 0: Ghost Database Setup

Ghost is a Postgres-as-a-service designed for agent workflows (https://ghost.build).

```bash
# Install Ghost CLI
curl -fsSL https://install.ghost.build | sh

# Authenticate
ghost login

# Create database
ghost create --name web-research

# Get connection string (use as DATABASE_URL)
ghost connect <db-id>
```

The `DATABASE_URL` from `ghost connect` is a standard Postgres connection string — works with both `psycopg2` and `pg` npm package unchanged.

## Phase 1: Python Scripts & DB Setup

### `scripts/requirements.txt`

```
anthropic
psycopg2-binary
python-dotenv
```

### `.env.example` (root)

```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...  # from `ghost connect <db-id>`
```

### `scripts/setup_db.py`

- Reads `DATABASE_URL` from env via `python-dotenv`
- Creates 3 tables if not exist:
  - `results` — id serial PK, topic text, url text, title text, content text, agent_id text, created_at timestamptz default now(), labeled bool default false
  - `labels` — id serial PK, result_id int FK -> results.id, labels jsonb, agent_id text, created_at timestamptz default now()
  - `agent_logs` — id serial PK, agent_id text, agent_type text, status text, message text, created_at timestamptz default now()

### `scripts/crawl.py`

- CLI: `--topic` (required), `--agents` (default 3), `--max-results` (default 50)
- Each agent gets a unique research angle (news, academic, practical, datasets, case studies, tutorials, opinion, historical)
- Uses `AsyncAnthropic` with `web_search_20260209` tool (dynamic filtering for better result quality):
  ```python
  tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 10}]
  ```
- **Connection management**: each agent creates its own `psycopg2` connection at startup (not shared) so transactions are isolated
- **Conversation loop** for `pause_turn`:
  - If `stop_reason == "pause_turn"`, append the assistant response to messages and continue
  - Exit when `stop_reason == "end_turn"`, agent has hit `max_results`, or a hard cap of 20 turns is reached (prevents runaways)
  - Parse JSON blocks from each response incrementally (before continuing), so results stream into the DB as they arrive
- System prompt instructs Claude to research from a specific angle and output JSON blocks: `{url, title, content}`
- Parses text blocks, extracts JSON via regex, inserts into `results` table
- **Error handling**:
  - Each agent's loop is wrapped in try/except — errors are logged to `agent_logs`, agent continues
  - On `429` rate limits: exponential backoff (`asyncio.sleep(2 ** attempt)`, max 3 retries)
  - If JSON parsing fails on a text block: skip it and log, don't crash the agent
- Logs activity to `agent_logs`
- Runs N agents in parallel via `asyncio.gather`

### `scripts/label.py`

- CLI: `--schema` (required, e.g. `"relevance:high/medium/low, type:article/video"`), `--agents` (default 3), `--batch-size` (default 5)
- **Connection management**: each agent creates its own `psycopg2` connection at startup — required for `FOR UPDATE SKIP LOCKED` to isolate work across agents
- Each agent loops:
  1. `SELECT ... FROM results WHERE labeled = false FOR UPDATE SKIP LOCKED LIMIT batch_size`
  2. If no rows, exit
  3. Prompt Claude to classify each result against the schema, return JSON labels
  4. Insert into `labels` table, mark result as labeled
  5. Log to `agent_logs`
- **Error handling**:
  - Each agent's loop is wrapped in try/except — errors are logged to `agent_logs`, agent continues to next batch
  - On `429` rate limits: exponential backoff (`asyncio.sleep(2 ** attempt)`, max 3 retries)
  - If Claude returns labels that don't match the schema: skip and log, don't insert garbage
- Uses `AsyncAnthropic` (no web search needed)
- Runs N agents in parallel via `asyncio.gather`
- DB calls via `asyncio.to_thread` (psycopg2 is sync)

## Phase 2: Next.js Dashboard

### `dashboard/package.json`

- Dependencies: `next`, `react`, `react-dom`, `pg`
- Dev deps: `typescript`, `@types/react`, `@types/node`, `@types/pg`

### `dashboard/lib/db.ts`

- Shared `pg.Pool` singleton using `DATABASE_URL` env var

### `dashboard/app/layout.tsx`

- Dark theme, monospace font (Geist Mono via next/font)

### `dashboard/app/globals.css`

- Terminal/hacker aesthetic: dark bg (#0a0a0a), green/cyan accents, monospace
- Styles for cards, progress bars, status dots, tables

### `dashboard/app/page.tsx`

- Client component, polls `/api/stats` and `/api/results` every 2s
- Sections:
  - **Stats bar**: total / labeled / unlabeled + progress bar
  - **Active agents**: cards with agent_id, type, status (colored dots)
  - **Activity log**: scrollable recent agent_logs
  - **Results table**: url, title, content (truncated), labels (colored badges), timestamp

### `dashboard/app/api/stats/route.ts`

- Returns: `{ total, labeled, unlabeled, agents[], recent_logs[] }`
- Queries: COUNT on results, latest status per agent_id, last 20 logs

### `dashboard/app/api/results/route.ts`

- Returns last 50 results LEFT JOIN labels
- `{ id, topic, url, title, content, labeled, labels, created_at }[]`

## Phase 3: Shell Script & Skill Spec

### `scripts/start_dashboard.sh`

```bash
#!/bin/bash
cd "$(dirname "$0")/../dashboard"
npm install
npm run dev
```

### `SKILL.md`

- Frontmatter skill spec describing the tool's purpose and usage

## Key Technical Decisions

- **`web_search_20260209`** — latest version with dynamic filtering, Claude filters search results before loading into context for better accuracy and lower token usage
- **Ghost** — agent-native Postgres hosting, no local DB setup needed, `ghost create` + `ghost connect` gives a connection string instantly
- **`psycopg2-binary` + `asyncio.to_thread`** — avoids asyncpg dependency while running agents concurrently; each agent gets its own connection for proper transaction isolation with `FOR UPDATE SKIP LOCKED`
- **`pg` npm package** — lightweight, no ORM for simple dashboard queries
- **Shared `DATABASE_URL`** — single env var for both Python and Node (from `ghost connect`)
- **`SELECT FOR UPDATE SKIP LOCKED`** — Postgres row-level locking for work queue, prevents double-labeling

## Verification

1. **DB**: `ghost psql <db-id>` to verify tables after `python scripts/setup_db.py`
2. **Crawl**: `source .venv/bin/activate && python scripts/crawl.py --topic "coral reef restoration" --agents 2 --max-results 10` -> check `results` and `agent_logs`
3. **Dashboard**: `bash scripts/start_dashboard.sh` -> open `localhost:3000`
4. **Label**: `python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 2` -> check `labels` table + dashboard updates

## Usage Flow

```bash
# 0. Database (one-time)
curl -fsSL https://install.ghost.build | sh
ghost login
ghost create --name web-research
# Copy the DATABASE_URL from `ghost connect <db-id>` into .env

# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/setup_db.py

# 2. Research
python scripts/crawl.py --topic "coral reef restoration" --agents 5

# 3. Watch live (run alongside crawl)
bash scripts/start_dashboard.sh

# 4. Label
python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3
```
