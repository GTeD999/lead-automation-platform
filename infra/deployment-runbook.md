# Deployment Runbook

## Server Paths

Main server path:

```text
/opt/novactiv-leads
```

Supabase Docker setup:

```text
/opt/novactiv-leads/compose/supabase-repo/docker
```

Secrets:

```text
/opt/novactiv-leads/compose/supabase-repo/docker/.env
```

Do not copy `.env` into the repository.

## Compose Command

Always include all four compose files:

```bash
cd /opt/novactiv-leads/compose/supabase-repo/docker
docker compose -f docker-compose.yml -f docker-compose.caddy.yml -f docker-compose.security.yml -f docker-compose.n8n.yml -f docker-compose.lead-ui.yml -f docker-compose.telegram.yml ps
```

Start or update:

```bash
cd /opt/novactiv-leads/compose/supabase-repo/docker
docker compose -f docker-compose.yml -f docker-compose.caddy.yml -f docker-compose.security.yml -f docker-compose.n8n.yml -f docker-compose.lead-ui.yml -f docker-compose.telegram.yml up -d
```

## Public URLs

- Supabase Studio: `http://45.92.174.232/`
- Supabase API gateway:
  - `http://45.92.174.232/rest/v1/`
  - `http://45.92.174.232/auth/v1/`
  - `http://45.92.174.232/storage/v1/`
- n8n: `http://45.92.174.232/n8n/`
- Lead intake UI: `http://45.92.174.232/leads/`

Supabase Studio is protected with Caddy basic auth using credentials from the server `.env`.
n8n uses `N8N_SECURE_COOKIE=false` temporarily because the project is currently running on HTTP by IP address.
n8n is mounted under `/n8n/`; Caddy must use `handle_path /n8n/*` so static assets and REST calls are proxied without the `/n8n` prefix.
Lead intake UI is protected with the same Caddy basic auth as Supabase Studio.

## Telegram Collector

Telegram collection uses a normal Telegram user account, not a bot.

Required server env values:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_PHONE
TELEGRAM_SOURCES
```

Start in dry-run mode:

```text
COLLECTOR_DRY_RUN=true
```

The first Telegram login requires an interactive code. Run the collector interactively once to create the session, then run it as a scheduled/background service.

## Security Shape

Publicly exposed ports:

- `80/tcp`
- `443/tcp`

Not publicly exposed:

- Supabase Postgres.
- Supavisor pooler.
- n8n internal port.
- Supabase internal services.

`docker-compose.security.yml` removes the Supavisor public port bindings.

## Database Migration

Applied migration:

```text
supabase/migrations/0001_initial_schema.sql
```

Key tables verified:

- `lead_sources`
- `lead_source_records`
- `leads`
- `properties`
- `presentations`

## Backups

Postgres backup script:

```text
/opt/novactiv-leads/scripts/backup-supabase-postgres.sh
```

Backup location:

```text
/opt/novactiv-leads/backups/postgres
```

Systemd timer:

```text
novactiv-supabase-backup.timer
```

Schedule:

```text
03:20 UTC daily
```

Manual backup:

```bash
/opt/novactiv-leads/scripts/backup-supabase-postgres.sh
```

## Health Checks

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/n8n/
curl -I http://127.0.0.1/leads/
docker compose -f docker-compose.yml -f docker-compose.caddy.yml -f docker-compose.security.yml -f docker-compose.n8n.yml -f docker-compose.lead-ui.yml -f docker-compose.telegram.yml ps
```

## Remaining Production Hardening

- Create non-root deployment user.
- Add SSH public keys.
- Disable root SSH after key access is verified.
- Disable password SSH after key access is verified.
- Add HTTPS after domain/DNS is ready.
- Add off-server backup target.
- Test restore procedure.
