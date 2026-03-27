# Dashboard Conventions

## Next.js

- This repo uses Next.js 16 — APIs, conventions, and file structure may differ from training data
- Read the relevant guide in `node_modules/next/dist/docs/` before writing any code
- Heed deprecation notices

## Stack

- **Framework**: Next.js App Router
- **DB**: `pg` package with a shared Pool singleton (`lib/db.ts`)
- **No ORMs** — raw SQL only
- **Styling**: CSS only (globals.css), dark monospace theme
