# Database and Supabase Agent

## Purpose

Own the data layer for Office Leads: Postgres schema, Supabase configuration, migrations, row level security, storage structure, and data quality rules. The agent keeps the database practical for the first milestone while leaving clear extension points for CRM workflows and automatic property presentations.

## Operating Principles

- Prefer simple normalized tables with explicit foreign keys, timestamps, and audit fields.
- Store raw source data before transforming it so collectors can be debugged and reprocessed.
- Separate lead identity, source evidence, events, scoring, and outreach history.
- Make deduplication deterministic where possible: normalized phone, email, Telegram username, VK URL, and source URL hashes.
- Treat all contact data as sensitive. Expose it only through approved roles and service workflows.
- Design for n8n and collectors to write safely through service roles or narrow RPC functions.
- Keep schema changes reversible, reviewed, and documented before deployment.

## Responsibilities

- Design and maintain tables for leads, sources, events, properties, media, presentations, blacklist, users, and roles.
- Configure Supabase Auth, Storage buckets, API access, and Row Level Security.
- Prepare SQL migrations, indexes, constraints, seed data, and rollback notes.
- Support deduplication, scoring, source traceability, opt-outs, and audit logs.
- Coordinate with Lead Collection, Normalization/Scoring, n8n, DevOps, and QA agents.

## Initial Schema Plan

### users and roles

Use Supabase Auth for authentication and keep application profile data in public tables.

- `profiles`: one row per auth user.
  - `id uuid primary key references auth.users(id)`
  - `full_name text`
  - `phone text`
  - `status text check (status in ('active','disabled'))`
  - `created_at timestamptz default now()`
  - `updated_at timestamptz default now()`
- `roles`: stable role catalog.
  - `id uuid primary key default gen_random_uuid()`
  - `code text unique not null`
  - `name text not null`
- `user_roles`: many-to-many role assignments.
  - `user_id uuid references profiles(id)`
  - `role_id uuid references roles(id)`
  - `created_at timestamptz default now()`
  - Primary key: `(user_id, role_id)`

Initial role codes: `admin`, `manager`, `collector`, `automation`, `viewer`.

### sources

Track where data came from and how it may be collected.

- `sources`
  - `id uuid primary key default gen_random_uuid()`
  - `name text not null`
  - `type text not null` such as `website`, `telegram`, `vk`, `map`, `form`, `partner`
  - `base_url text`
  - `collection_policy text not null default 'manual_review'`
  - `is_active boolean default true`
  - `rate_limit_per_hour integer`
  - `created_at timestamptz default now()`
  - `updated_at timestamptz default now()`

### leads

Store one canonical record per potential customer or company contact.

- `leads`
  - `id uuid primary key default gen_random_uuid()`
  - `lead_type text check (lead_type in ('person','company','unknown')) default 'unknown'`
  - `display_name text`
  - `company_name text`
  - `phone_raw text`
  - `phone_normalized text`
  - `email text`
  - `telegram_username text`
  - `vk_url text`
  - `city text`
  - `intent text`
  - `object_type text`
  - `budget_min numeric`
  - `budget_max numeric`
  - `urgency text`
  - `status text default 'new'`
  - `score integer default 0`
  - `score_reason text`
  - `dedupe_key text`
  - `assigned_to uuid references profiles(id)`
  - `first_seen_at timestamptz default now()`
  - `last_seen_at timestamptz default now()`
  - `created_at timestamptz default now()`
  - `updated_at timestamptz default now()`

Recommended indexes:

- Unique partial index on `phone_normalized` where not null.
- Indexes on `email`, `telegram_username`, `vk_url`, `dedupe_key`, `status`, `assigned_to`, and `created_at`.

### lead_source_records

Preserve source evidence and extraction details separately from canonical leads.

- `lead_source_records`
  - `id uuid primary key default gen_random_uuid()`
  - `lead_id uuid references leads(id)`
  - `source_id uuid references sources(id)`
  - `source_url text`
  - `source_url_hash text`
  - `raw_text text`
  - `raw_payload jsonb`
  - `extracted_contacts jsonb`
  - `confidence numeric check (confidence >= 0 and confidence <= 1)`
  - `collected_at timestamptz default now()`
  - `collector_run_id uuid`

Recommended indexes:

- Unique index on `(source_id, source_url_hash)` where `source_url_hash` is not null.
- GIN index on `raw_payload` if JSON search becomes necessary.

### events

Represent lead lifecycle changes, n8n actions, outreach attempts, scoring updates, and audit history.

- `events`
  - `id uuid primary key default gen_random_uuid()`
  - `lead_id uuid references leads(id)`
  - `event_type text not null`
  - `actor_type text not null` such as `user`, `collector`, `n8n`, `system`
  - `actor_id uuid`
  - `payload jsonb`
  - `created_at timestamptz default now()`

Recommended indexes: `lead_id`, `event_type`, `created_at`.

### blacklist

Prevent repeated processing or outreach for disallowed contacts.

- `blacklist_entries`
  - `id uuid primary key default gen_random_uuid()`
  - `entry_type text not null` such as `phone`, `email`, `telegram`, `vk`, `domain`, `company`
  - `entry_value text not null`
  - `normalized_value text not null`
  - `reason text not null`
  - `created_by uuid references profiles(id)`
  - `expires_at timestamptz`
  - `created_at timestamptz default now()`

Recommended index: unique index on `(entry_type, normalized_value)`.

### properties

Prepare for future property matching and presentation generation.

- `properties`
  - `id uuid primary key default gen_random_uuid()`
  - `title text not null`
  - `property_type text`
  - `deal_type text` such as `sale`, `rent`
  - `city text`
  - `address text`
  - `area_sqm numeric`
  - `rooms integer`
  - `price numeric`
  - `currency text default 'RUB'`
  - `description text`
  - `status text default 'draft'`
  - `created_by uuid references profiles(id)`
  - `created_at timestamptz default now()`
  - `updated_at timestamptz default now()`

Recommended indexes: `city`, `property_type`, `deal_type`, `status`, `price`.

### media

Track files stored in Supabase Storage.

- `media`
  - `id uuid primary key default gen_random_uuid()`
  - `owner_type text not null` such as `property`, `presentation`, `lead`
  - `owner_id uuid not null`
  - `bucket text not null`
  - `storage_path text not null`
  - `media_type text` such as `photo`, `floorplan`, `document`
  - `mime_type text`
  - `sort_order integer default 0`
  - `metadata jsonb`
  - `created_at timestamptz default now()`

Recommended index: `(owner_type, owner_id)`.

Storage buckets:

- `property-media`: private by default.
- `presentation-files`: private by default.
- `lead-attachments`: private by default.

### presentations

Store generated property decks and their generation status.

- `presentations`
  - `id uuid primary key default gen_random_uuid()`
  - `lead_id uuid references leads(id)`
  - `property_id uuid references properties(id)`
  - `title text not null`
  - `status text default 'draft'`
  - `template_code text`
  - `output_bucket text`
  - `output_path text`
  - `generation_payload jsonb`
  - `generated_by uuid references profiles(id)`
  - `generated_at timestamptz`
  - `created_at timestamptz default now()`
  - `updated_at timestamptz default now()`

Recommended indexes: `lead_id`, `property_id`, `status`.

## RLS Principles

- Enable RLS on all application tables before production use.
- Default deny: create explicit policies for each role and workflow.
- Use Supabase service role only on trusted backend jobs, collectors, and n8n server-side workflows.
- Keep anonymous access disabled for sensitive tables.
- Managers can read assigned leads and create events for those leads.
- Admins can read and manage all application data.
- Collectors can insert source records and candidate leads only through service role or validated RPC functions.
- Automation can read new leads, update scoring/status fields, and insert events through service role or narrow RPC functions.
- Viewers can read non-sensitive operational summaries only after dedicated views are created.
- Do not expose raw payloads, contact fields, blacklist data, or auth-related tables to public clients.

Suggested helper functions:

- `has_role(user_id uuid, role_code text) returns boolean`
- `is_admin() returns boolean`
- `can_access_lead(lead_id uuid) returns boolean`

## Migration Principles

- Store migrations in versioned SQL files, one logical change per migration.
- Use forward-only migrations for production; include rollback notes in comments or adjacent docs.
- Name migrations with timestamp and purpose, for example `20260506_001_initial_leads_schema.sql`.
- Separate schema, indexes, RLS policies, seed roles, and storage policy changes when they are large enough to review independently.
- Never edit an already-applied migration in production. Add a new migration instead.
- Add constraints as early as possible, but use `not valid` and backfills for large existing tables.
- Include indexes required by foreign keys, deduplication, n8n polling, and manager dashboards.
- Test migrations on a disposable database before applying to the server.
- Record deployment order, required environment variables, and verification queries.

## First Milestone Database Tasks

1. Create migrations for `sources`, `leads`, `lead_source_records`, `events`, `blacklist_entries`, `profiles`, `roles`, and `user_roles`.
2. Seed initial roles: `admin`, `manager`, `collector`, `automation`, `viewer`.
3. Add deduplication indexes for normalized contact fields and source URL hashes.
4. Enable RLS with admin, manager, collector, and automation policies.
5. Create one insertion path for the first conservative collector.
6. Create one n8n-safe path for deduplicate, score, status update, and manager notification events.
7. Add verification SQL for table existence, indexes, RLS status, and sample insert/read behavior.

## Deferred Until Needed

- Advanced property matching and presentation recommendations.
- Public presentation sharing links.
- Full CRM pipeline stages and deal tracking.
- Multi-agency tenancy.
- Analytics marts and dashboard materialized views.
