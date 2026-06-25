# Lead Automation Platform

A **self-hosted lead generation and automation platform** for agencies that need lawful contact collection, scoring, manager workflows, and n8n-driven pipelines — with Supabase as the system of record.

Designed as a modular monorepo: collectors write to Postgres, n8n orchestrates follow-ups, and React/Python services provide UIs and tooling.

## Highlights

- **Supabase-first** — leads, events, scoring, and deduplication in PostgreSQL
- **n8n automation** — notify managers, route by score, trigger downstream jobs
- **Multiple collectors** — web forms, Telegram user parsing, B2B directory actors (Apify)
- **Lead Intelligence UI** — React dashboard for exploring and managing lead data
- **Presentation pipeline** (foundation) — property tables, PDF/PPTX generator, WordPress plugin stub
- **Documented roadmap** — phased delivery from server baseline to scale

## Architecture

```
                    ┌─────────────────┐
  Public sources ──►│ Lead collectors │──┐
  Web forms      ──►│ (Python)        │  │
  Telegram MTProto   └─────────────────┘  │
                                           ▼
                              ┌────────────────────────┐
                              │ Supabase (PostgreSQL)  │
                              │ leads · events · scores│
                              └───────────┬────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ┌──────────┐         ┌──────────────┐      ┌───────────────┐
             │ n8n      │         │ Lead Intel   │      │ Presentation  │
             │ workflows│         │ UI (React)   │      │ generator     │
             └──────────┘         └──────────────┘      └───────────────┘
```

## Repository layout

```
supabase/migrations/     SQL schema (lead intelligence, intent scenarios)
services/
  lead-intake-ui/        Public lead capture (Python)
  lead-intelligence-ui/  Manager dashboard (React + Vite)
  telegram-user-collector/  Telegram source parser
  presentation-generator/   Branded PDF/PPTX from property data
workflows/               n8n workflow templates (JSON)
wordpress-plugin/        Optional WP integration for presentations
infra/                   Server baseline & deployment runbook
docs/                    Agent playbooks (devops, database)
designpresentation/      HTML/CSS presentation template assets
```

## Features by phase

### Implemented / in repo

- Postgres schema migrations for leads and intelligence scoring
- Lead Intelligence React UI with charts and filters
- Telegram user collector with configurable sources and dry-run
- Presentation generator (Python) with styled output
- n8n workflow template for property presentations
- Deployment and agent documentation

### Roadmap (see `roadmap.md`)

1. **Core platform** — Supabase + n8n + reverse proxy + backups  
2. **Lead MVP** — deduplication, scoring v1, manager notifications  
3. **Manager workflow** — statuses, opt-out, templates, reporting  
4. **Presentations** — property-approved → generate PDF → notify  
5. **Scale** — monitoring, rate limits, multi-tenant hardening  

## Tech stack

| Component | Technology |
|-----------|------------|
| Database | PostgreSQL via Supabase (self-hosted) |
| Automation | n8n |
| Collectors | Python 3.11+ |
| Manager UI | React, TypeScript, Vite, Recharts |
| External data | Apify actors (optional), Telegram MTProto |
| Infra | Docker Compose, Ubuntu, reverse proxy |

## Getting started

### 1. Environment

```bash
cp .env.example .env
# Generate secrets for POSTGRES_PASSWORD, JWT_SECRET, N8N_ENCRYPTION_KEY, etc.
```

### 2. Supabase + n8n (production-style)

Follow `infra/deployment-runbook.md` for Docker Compose deployment on a VPS. For local experiments, point `SUPABASE_URL` at a local or cloud Supabase instance.

### 3. Lead Intelligence UI

```bash
cd services/lead-intelligence-ui
npm install
npm run dev
```

Or use the bundled compose file:

```bash
docker compose -f services/lead-intelligence-ui/docker-compose.lead-intelligence.yml up -d
```

### 4. Telegram collector

```bash
cd services/telegram-user-collector
pip install -r requirements.txt
# Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SOURCES in .env
python -m src.telegram_user_collector
```

Set `COLLECTOR_DRY_RUN=true` until Supabase credentials are configured.

## Key environment variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Database & API access |
| `N8N_*` | Automation server auth and encryption |
| `TELEGRAM_*` | MTProto collector credentials and sources |
| `APIFY_*` | Optional B2B directory scraping actor |
| `COLLECTOR_DRY_RUN` | Log-only mode for collectors |

Full list: `.env.example`

## Data & compliance principles

- Collect only **public or consent-based** contact signals  
- Store source URL, timestamp, and raw text for audit  
- Deduplicate by normalized phone / email / messenger handle  
- Approval-based outbound until opt-out handling is proven  

## Security

- No production credentials, phone numbers, or lead exports in git  
- `.env` and local data directories are gitignored  
- Use `COLLECTOR_DRY_RUN` and separate staging Supabase for development  

## Related docs

- `roadmap.md` — product phases  
- `agents.md` — multi-agent delivery plan  
- `infra/server-baseline.md` — server hardening checklist  
- `docs/database-agent.md` — schema ownership notes  

## License

Portfolio / demonstration project.
