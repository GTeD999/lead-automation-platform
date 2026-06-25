# Architecture

## Components

- Supabase: system of record for leads, properties, media metadata, events, and generated presentations.
- n8n: workflow orchestration for lead intake, scoring, manager notifications, follow-ups, and presentation generation triggers.
- Lead collectors: small services or scheduled jobs that collect allowed public signals and send normalized payloads to Supabase.
- Normalization/scoring service: shared logic for contacts, deduplication, classification, and quality scoring.
- Presentation generator: future service that turns property records and media into branded PDF/PPTX materials.
- Reverse proxy: one entry point for HTTP/S access.

## Data Flow

```text
Source -> Collector -> Raw lead payload -> Supabase -> n8n trigger -> scoring/enrichment -> manager workflow
```

Future presentation flow:

```text
Property data + media -> Supabase -> n8n trigger -> generator service -> Supabase Storage -> manager notification
```

## Deployment Shape

Start with one Ubuntu server:

- Docker Compose for all services.
- Isolated Docker networks.
- Named volumes for persistent data.
- Backups to local archive first, remote backup later.
- IP-based access first, domain and HTTPS later.

## Security Baseline

- Replace root password workflow with SSH keys and a deployment user.
- Use firewall allowlist.
- Keep admin services behind reverse proxy or private ports.
- Generate unique secrets for every service.
- Store secrets in `.env` files on the server, not in the repository.
- Rotate credentials after initial setup.

