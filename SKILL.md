---
name: web-research-labeler
description: Autonomous web research tool — spins up parallel Claude agents to search, crawl, and label web results on any topic, stored in Ghost (Postgres) with a live Next.js dashboard.
---

# web-research-labeler

Research any topic with parallel Claude agents. Results are stored in Postgres (via Ghost) and visible in a live dashboard.

## Prerequisites

- Ghost CLI installed (`curl -fsSL https://install.ghost.build | sh`)
- A Ghost database created (`ghost create --name web-research`)
- `ANTHROPIC_API_KEY` and `DATABASE_URL` set in `.env`
- Python deps installed (`pip install -r scripts/requirements.txt`)
- Tables created (`python scripts/setup_db.py`)

## Commands

### Crawl a topic

```bash
python scripts/crawl.py --topic "<topic>" --agents 3 --max-results 50
```

Launches parallel agents that web-search from different angles (news, academic, practical, etc.) and stream results into the `results` table.

### Label results

```bash
python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3
```

Parallel agents classify unlabeled results against your schema using `SELECT FOR UPDATE SKIP LOCKED` to avoid double-labeling.

### Live dashboard

```bash
bash scripts/start_dashboard.sh
```

Opens a Next.js dashboard at `localhost:3000` that polls the database every 2s — shows stats, active agents, activity log, and results with label badges.

### Export results

```bash
python scripts/export.py                          # export all to export.json
python scripts/export.py --labeled-only -o out.json  # only labeled results
python scripts/export.py --topic "coral reef restoration"
```

Dumps results with their labels to a JSON file that can be read by the calling agent.

### Inspect the database

```bash
ghost psql <db-id>
```

## Typical workflow

1. `python scripts/crawl.py --topic "coral reef restoration" --agents 5`
2. `bash scripts/start_dashboard.sh` (in another terminal)
3. `python scripts/label.py --schema "relevance:high/medium/low, type:article/study/news" --agents 3`
4. Watch results and labels appear live in the dashboard
5. `python scripts/export.py --labeled-only -o research.json` — export for downstream use
