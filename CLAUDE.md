# web-research-labeler

Autonomous web research tool using parallel Claude agents with Ghost (Postgres) storage and a live Next.js dashboard.

## Architecture

- **`scripts/`** — Python CLI tools (crawl, label, DB setup)
- **`dashboard/`** — Next.js App Router dashboard (TypeScript)
- **Ghost** — managed Postgres database (https://ghost.build), accessed by both Python and Node via `DATABASE_URL`

## Environment Setup

```bash
# 1. Install Ghost CLI and create database
curl -fsSL https://install.ghost.build | sh
ghost login
ghost create --name web-research
# Get connection string:
ghost connect <db-id>

# 2. Copy env file, paste DATABASE_URL from ghost connect
cp .env.example .env

# 3. Install Python deps
pip install -r scripts/requirements.txt

# 4. Create tables
python scripts/setup_db.py

# 5. Install dashboard deps
cd dashboard && npm install
```

Required env vars:

- `ANTHROPIC_API_KEY` — Claude API key
- `DATABASE_URL` — Postgres connection string from `ghost connect <db-id>`

## Running

```bash
# Crawl a topic
python scripts/crawl.py --topic "coral reef restoration" --agents 3 --max-results 50

# Start dashboard (polls DB every 2s)
bash scripts/start_dashboard.sh

# Label results
python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3

# Inspect DB directly
ghost psql <db-id>
```

## Code Conventions

### Shared Patterns

- `DATABASE_URL` env var is the single source of truth for DB connection (from Ghost)
- All timestamps are `timestamptz` with `default now()`
- Agent IDs are generated as `{type}-{uuid[:8]}` (e.g. `crawler-a1b2c3d4`)
- No ORMs — raw SQL only in both Python and TypeScript

### Ghost Database

- Ghost is Postgres under the hood — all standard SQL and `psycopg2`/`pg` patterns work unchanged
- Use `ghost psql <db-id>` for interactive SQL sessions
- Use `ghost fork <db-id>` to create a copy for safe experimentation
- Use `ghost schema <db-id>` to inspect table definitions

## DB Schema

Three tables:

- **`results`** — crawled web results (topic, url, title, content, agent_id, labeled flag)
- **`labels`** — classification labels per result (result_id FK, labels JSONB)
- **`agent_logs`** — agent activity log (agent_id, agent_type, status, message)

## See Also

- `PLAN.md` — full implementation plan with phases and verification steps
