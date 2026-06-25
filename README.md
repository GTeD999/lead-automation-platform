# Novactiv Leads

Lead generation and automation platform for a real estate agency — public lead collection, contact normalization, scoring, and manager workflows.

## Features

- Lawful public lead collection pipelines
- Supabase as system of record
- n8n workflow automation
- Contact normalization and lead scoring
- Manager dashboard and workflows
- B2B Lead Intelligence UI

## Tech stack

| Layer | Technology |
|-------|-----------|
| Database | Supabase (PostgreSQL) |
| Automation | n8n |
| UI | React dashboard |
| Infra | Docker, Ubuntu server |

## Project structure

```
infra/                          Docker deployment
supabase/migrations/            Database migrations
services/lead-intelligence-ui/  Dashboard and API
workflows/                      Exported n8n workflows
docs/                           Architecture and agent docs
```

## Getting started

```bash
cp .env.example .env
# Configure Supabase and n8n credentials
docker compose up -d
```

## Security

Source code only — no credentials, API keys, or client data included.

## License

Private / portfolio project.
