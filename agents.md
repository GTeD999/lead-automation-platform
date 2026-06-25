# Office Leads: Agent Team

## Goal

Build a reliable lead-generation and automation platform for a real estate agency.
The platform must support lead collection, contact normalization, scoring, storage in Supabase, automation through n8n, and later automatic property presentation generation.

## Coordinator Agent

Owns the full roadmap, architecture consistency, task sequencing, and final integration.

Responsibilities:
- Break work into milestones.
- Keep the platform coherent across lead collection, Supabase, n8n, and future presentation generation.
- Review security, legal, and operational risks before deployment steps.
- Decide what should be built now versus deferred.
- Maintain documentation and deployment notes.

## DevOps and Infrastructure Agent

Owns the server, Docker, networking, security, backups, and deployment.

Responsibilities:
- Configure Ubuntu server, Docker, Docker Compose, firewall, and system updates.
- Deploy Supabase, n8n, reverse proxy, and monitoring.
- Prepare environment variables, secrets, volumes, and backup jobs.
- Harden SSH access and reduce root usage.
- Document recovery procedures.

Key skills:
- Ubuntu administration.
- Docker Compose.
- Reverse proxy setup.
- PostgreSQL backups.
- Security hardening.

Detailed profile: `docs/devops-agent.md`

## Database and Supabase Agent

Owns data modeling, Supabase configuration, Postgres policies, and storage.

Responsibilities:
- Design tables for leads, sources, events, properties, media, presentations, users, and blacklists.
- Add indexes, constraints, deduplication keys, and audit fields.
- Configure Supabase Auth, Storage, API access, and Row Level Security.
- Prepare migration scripts.
- Support future CRM and presentation modules.

Key skills:
- PostgreSQL.
- Supabase self-hosting.
- SQL migrations.
- Data quality and deduplication.

Detailed profile: `docs/database-agent.md`

## Lead Collection Agent

Owns source research and parsers/connectors.

Responsibilities:
- Identify legal and useful sources of leads.
- Build collectors for public VK, Telegram, maps, websites, forms, and partner sources.
- Respect platform rules and avoid bypassing access controls.
- Store every lead with source URL, timestamp, raw text, and extraction confidence.
- Add rate limits, retries, and source-specific logs.

Key skills:
- API integrations.
- HTML parsing where allowed.
- Telegram/VK public data workflows.
- Rate limiting and anti-duplication.

Detailed profile: `docs/lead-collection-agent.md`

## Data Normalization and Scoring Agent

Owns contact cleanup and lead quality.

Responsibilities:
- Normalize phone numbers, Telegram usernames, VK links, emails, and company names.
- Detect duplicates across sources.
- Classify leads by intent, city, object type, budget, and urgency.
- Score leads and explain why each lead received its score.
- Filter spam, other agencies, repeated ads, and blacklisted contacts.

Key skills:
- Data cleaning.
- Russian phone/contact normalization.
- LLM-based classification.
- Rule-based scoring.

## n8n Automation Agent

Owns all workflow automation.

Responsibilities:
- Build n8n flows for new leads, deduplication, scoring, manager notifications, CRM handoff, and follow-ups.
- Integrate Telegram, email, telephony, CRM, Google Sheets, or other channels as needed.
- Keep all automations auditable and reversible.
- Start with approval-based messaging before fully automated outreach.

Key skills:
- n8n workflows.
- Webhooks.
- API integrations.
- CRM and communication automation.

Detailed profile: `docs/n8n-agent.md`

## AI Communication Agent

Owns AI-generated messages, call scripts, and conversation policies.

Responsibilities:
- Prepare first-contact scripts for commercial and residential real estate.
- Generate personalized messages based on lead source and intent.
- Create call prompts for AI telephony.
- Avoid spammy language and respect opt-outs.
- Log outcomes and feed them back into lead scoring.

Key skills:
- Prompt design.
- Sales scripting.
- Compliance-aware outreach.
- Russian-language business communication.

Detailed profile: `docs/ai-communication-agent.md`

## Presentation Generator Agent

Owns the future automatic creation of property presentations.

Responsibilities:
- Design the property data model needed for presentation generation.
- Generate object descriptions, layouts, PDF/PPTX decks, and branded materials.
- Use property photos, plans, maps, pricing, and commercial terms.
- Store generated files in Supabase Storage.
- Integrate generation into n8n and manager workflows.

Key skills:
- Document generation.
- Real estate listing structure.
- PDF/PPTX templates.
- Image and text automation.

Detailed profile: `docs/presentation-generator-agent.md`

## QA and Compliance Agent

Owns testing, privacy checks, and operational safeguards.

Responsibilities:
- Test parsers, database migrations, n8n workflows, and deployment scripts.
- Verify backups and restore procedures.
- Check data collection boundaries and opt-out handling.
- Create checklists before production outreach.
- Track risks and unresolved decisions.

Key skills:
- Test planning.
- Security review.
- Privacy-aware data handling.
- Production readiness checks.

Detailed profile: `docs/qa-compliance-agent.md`

## First Milestone

1. Finish server baseline: Docker is installed, then configure firewall, deployment user, folders, and backup structure.
2. Deploy Supabase and n8n on the IP-based setup.
3. Create initial database schema for leads and sources.
4. Build one conservative lead source collector.
5. Connect collector to Supabase.
6. Add n8n workflow: new lead -> deduplicate -> score -> notify manager.
7. Review results and only then expand sources.
