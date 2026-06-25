# Security Notes

## Current State

- SSH access details are stored in `access.md`.
- Docker and Docker Compose are installed on the server.
- UFW is enabled and allows SSH, HTTP, and HTTPS.
- Docker log rotation is configured.
- Supabase and n8n are not deployed yet.

## Required Before Production Data

- Create a non-root deployment user.
- Add SSH keys for approved operators.
- Disable password SSH after key login is verified.
- Disable direct root SSH after the deployment user is verified.
- Enable firewall rules for SSH, HTTP, and HTTPS only.
- Generate unique secrets for Supabase and n8n.
- Keep `.env` files only on the server.
- Configure backups before storing real leads.
- Rotate the root password after initial setup.

## Secret Handling

- Do not commit `access.md`.
- Do not paste service role keys into n8n workflow descriptions.
- Do not export n8n workflows with credentials.
- Do not store cookies or platform tokens in lead records.
- Do not store raw backup archives in the project repository.
