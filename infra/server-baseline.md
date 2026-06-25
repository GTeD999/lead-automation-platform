# Server Baseline

## Verified Server Facts

- Host: `45.92.174.232`
- OS: Ubuntu 24.04.4 LTS
- CPU: 8 cores
- RAM: 15 GiB
- Disk: about 213 GB
- Docker: installed
- Docker Compose: installed

## Completed

- Docker installed.
- Docker Compose installed.
- Docker daemon log rotation configured:
  - max size: 10 MB
  - max files: 5
- Project directory created at `/opt/novactiv-leads`.
- Environment directory created at `/opt/novactiv-leads/env`.
- Firewall enabled through UFW.
- Allowed inbound ports:
  - `22/tcp` SSH
  - `80/tcp` HTTP
  - `443/tcp` HTTPS
- Default incoming traffic denied.
- Default outgoing traffic allowed.
- Supabase self-hosted stack deployed.
- n8n deployed at `/n8n/`.
- Supabase initial database migration applied.
- Daily Postgres backup timer configured.

## Server Directory Layout

```text
/opt/novactiv-leads/
  backups/
    postgres/
    storage/
    n8n/
  compose/
  env/
  logs/
  scripts/
```

## Not Done Yet

- Dedicated deployment user.
- SSH key access.
- Disabling password SSH.
- Disabling direct root SSH.
- Restore test.
-- Off-server backup target.
-- Domain and HTTPS.

## Next Safe Step

Create a deployment user after an operator SSH public key is available. Do not disable root login or password authentication until the new login path is verified in a separate SSH session.
