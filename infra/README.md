# Infrastructure

This folder will contain the production Docker Compose setup for the server.

Current server facts:
- Host: 45.92.174.232
- OS: Ubuntu 24.04.4 LTS
- CPU: 8 cores
- RAM: 15 GiB
- Disk: about 213 GB
- Docker: installed
- Docker Compose: installed

Planned services:
- Reverse proxy.
- Supabase self-hosted stack.
- n8n.
- Backup jobs.
- Lead collector workers.
- Future presentation generator.

Secrets must stay on the server in `.env` files and must not be committed.
