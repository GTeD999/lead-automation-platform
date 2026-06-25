# Office Leads Roadmap

## Product Vision

Build a server-based platform that collects lawful public lead signals, stores clean contacts in Supabase, routes work through n8n, and later generates property presentations from structured object data.

## Operating Principles

- Collect only data that is public, permitted by source rules, or submitted directly by the user.
- Store the source URL, timestamp, raw text, and processing history for every lead.
- Keep outreach approval-based until quality, legality, and opt-out handling are proven.
- Treat Supabase as the system of record.
- Treat n8n as the automation layer, not as the primary database.
- Build modules that can also support property presentation generation later.

## Phase 0: Server Baseline

Status: in progress.

Deliverables:
- Docker and Docker Compose installed.
- Firewall configured for SSH, HTTP, and HTTPS.
- Dedicated deployment user created.
- Root login and password SSH reduced after key-based access is ready.
- Project directories created under `/opt/office`.
- Backup directory and restore procedure documented.

Notes:
- Docker and Docker Compose were installed on the server.
- Firewall is enabled and allows `22/tcp`, `80/tcp`, and `443/tcp`.
- Project directories were created under `/opt/office-leads`.
- Supabase and n8n were deployed through Docker Compose.
- Initial schema migration was applied.
- Daily local Postgres backup is configured.

## Phase 1: Core Platform

Deliverables:
- Self-hosted Supabase deployed.
- n8n deployed.
- Reverse proxy configured for IP-based access first.
- Postgres backup job configured.
- Initial Supabase schema applied.
- Basic healthcheck commands documented.

## Phase 2: Lead MVP

Deliverables:
- First conservative lead collector.
- Contact extraction for phone, email, Telegram, VK, and source links.
- Deduplication by normalized contact values.
- Lead scoring v1.
- n8n workflow: new lead -> deduplicate -> score -> notify manager.

Recommended first sources:
- Website forms and landing pages.
- Public Telegram channels/chats where messages are accessible and rules allow collection.
- Public VK posts or comments where contacts are explicitly posted.
- Company websites and map listings for commercial real estate outreach.

## Phase 3: Manager Workflow

Deliverables:
- Manager status pipeline.
- Contact attempt history.
- Blacklist and opt-out handling.
- Message templates.
- Approval-based outbound messages.
- Reporting by source, status, and conversion.

## Phase 4: Presentation Generator Foundation

Deliverables:
- Property tables and media storage ready.
- Branded presentation template selected.
- PDF/PPTX generation proof of concept.
- n8n trigger: property approved -> generate presentation -> notify manager.

## Phase 5: Scale and Reliability

Deliverables:
- More source connectors.
- Worker queues.
- Monitoring.
- Alerting.
- Backup restore test.
- Source-specific rate limits.
- Compliance checklist before outbound automation.
