# Python Scripts Conventions

## Async Patterns

- Use `AsyncAnthropic` client (not sync `Anthropic`)
- `asyncio.gather` for parallel agents
- `psycopg2-binary` with `asyncio.to_thread` for non-blocking DB calls
- Wrap entire transactional sequences (e.g. `SELECT FOR UPDATE` → process → `INSERT`/`UPDATE`) in a single `asyncio.to_thread` call to preserve row locks

## Web Search Tool

```python
tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 10}]
```

- Handle `pause_turn` stop reason: append assistant response to messages, send `{"role": "user", "content": "Continue searching."}` to continue
- Extract structured results from Claude's text response via regex

## CLI

- `argparse` for all scripts
- Common flags: `--topic`, `--agents`, `--schema`, `--batch-size`, `--max-results`

## DB

- No ORMs — raw SQL with parameterized queries (`%s` placeholders)
- Agent IDs: `{type}-{uuid[:8]}` (e.g. `crawler-a1b2c3d4`)
- All timestamps are `timestamptz` with `default now()`
- `DATABASE_URL` from env via `python-dotenv`
