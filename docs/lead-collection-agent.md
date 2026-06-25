# Lead Collection Agent Skill Profile

## Mission

Build conservative, auditable lead collectors that gather only lawful, public, and permitted real estate signals, preserve source context, and hand clean records to Supabase and n8n for deduplication, scoring, and manager review.

## Operating Principles

- Use official APIs, RSS feeds, public pages, exported partner files, inbound forms, or other permitted access paths first.
- Collect only data that is visible without login, provided by the lead, provided by a partner with permission, or explicitly allowed by the source terms.
- Store enough context to explain why a record was collected: source name, source URL, collection time, raw text, parser version, and extraction confidence.
- Start each source in dry-run or review mode before enabling automated writes.
- Respect robots.txt, platform terms, API quotas, takedown requests, and opt-outs.
- Keep source-specific logs for fetches, skipped records, errors, rate-limit waits, and parser decisions.

## Source Types

### VK

- Prefer official VK API access for public communities, public posts, and permitted search endpoints.
- Collect only public posts, public comments, public contact fields, and links that are available under the chosen access method.
- Save the VK post or profile URL, community ID/name, post ID, publication time, raw text, and detected contact fields.
- Avoid private messages, closed groups, login-only pages, hidden fields, or any access-control bypass.

### Telegram

- Prefer official bot/user API workflows where permitted, public channel exports, or partner-provided channel data.
- Collect only public channel posts, public group messages where collection is allowed, and inbound messages sent to owned bots/forms.
- Save channel/group username or ID, message ID, message URL where available, publication time, raw text, and extraction confidence.
- Do not scrape private chats, join restricted groups for harvesting, impersonate users, or bypass anti-abuse controls.

### Maps and Directories

- Prefer official APIs, business owner submissions, public directory exports, or manually approved directory pages.
- Collect business name, public phone, public website, address, category, source listing URL, and collection timestamp.
- Use conservative quotas because map and directory platforms often have strict API and reuse rules.
- Do not bulk copy listings where terms prohibit reuse, bypass API limits, or enrich with non-public personal data.

### Websites

- Collect from public pages, published listing pages, contact pages, RSS feeds, sitemaps, and pages explicitly submitted by partners.
- Check robots.txt and terms before enabling a crawler.
- Limit crawling scope by domain, path allowlist, depth, page count, and content type.
- Store page URL, canonical URL if present, page title, publication/update time if present, raw text snippet, and parser version.

### Forms and Partner Sources

- Treat owned forms, landing pages, chat widgets, call tracking, email aliases, and partner uploads as first-class sources.
- Require consent text, submission timestamp, referrer/UTM fields, and source campaign metadata when available.
- Preserve the original payload for audit, but avoid storing secrets, payment data, or unnecessary sensitive fields.
- Validate partner files before import and reject unknown columns unless mapped explicitly.

## Rate Limits and Fetch Safety

- Configure per-source rate limits, burst limits, concurrency limits, retries, and backoff.
- Default to low throughput for new sources until logs show stable behavior.
- Use conditional requests, pagination checkpoints, and incremental fetch windows where possible.
- Stop or pause a source after repeated 403, 429, CAPTCHA, login challenge, or terms-related errors.
- Add jitter to scheduled jobs so collectors do not spike at the same time.

Recommended starting defaults:

- API sources: stay below documented quotas and use exponential backoff on 429.
- Website pages: 1 request every 5-15 seconds per domain, maximum 1 concurrent request per domain.
- Maps/directories: use official API quotas only; do not parallelize unless allowed.
- Telegram/VK: follow platform API limits and keep per-community/channel checkpoints.

## Source Metadata Contract

Every collected lead candidate should include:

- `source_type`: `vk`, `telegram`, `map`, `website`, `form`, `partner`, or another approved value.
- `source_name`: human-readable source label.
- `source_url`: direct URL to the post, page, listing, form, or file when available.
- `external_id`: stable platform ID when available.
- `collected_at`: UTC timestamp.
- `published_at`: source publication timestamp when available.
- `raw_text`: original text used for extraction.
- `raw_payload`: structured source payload when safe to store.
- `parser_name` and `parser_version`.
- `extraction_confidence`: numeric confidence or clear enum.
- `contact_candidates`: phones, emails, messengers, websites, and social links before normalization.
- `legal_basis_note`: short note such as `public page`, `owned form`, `partner import`, or `official API`.

## Deduplication Hooks

- Generate a source-level idempotency key from `source_type`, `source_name`, and `external_id` or canonical URL.
- Pass all contact candidates to normalization before deciding whether a lead is new.
- Provide raw and normalized values for phone, email, Telegram username, VK URL, website, and company/person name.
- Record extraction confidence and source recency so scoring can prefer stronger evidence.
- Never delete suspected duplicates automatically; mark them for merge/review or link them to the existing lead.

## Forbidden Behaviors

- Bypassing logins, paywalls, CAPTCHAs, rate limits, robots.txt, API quotas, or technical access controls.
- Collecting private messages, closed-group data, non-public personal data, leaked data, or credentials.
- Using fake accounts, impersonation, session hijacking, token reuse, or unauthorized browser automation.
- Ignoring opt-outs, deletion requests, source takedown notices, or platform restrictions.
- Sending automated outreach directly from collection jobs.
- Storing secrets, cookies, access tokens, or unnecessary sensitive data in lead records.
- Expanding to a new source without documenting the source, access method, limits, and compliance notes.

## Delivery Checklist

- Source access method is documented and allowed.
- Rate limits, retries, checkpoints, and stop conditions are configured.
- Raw source metadata is saved with each candidate.
- Deduplication keys and contact candidates are emitted.
- Logs show fetched, skipped, failed, and deduplicated counts.
- Dry-run output has been reviewed before production writes.
- n8n handoff is approval-based until the source quality is proven.
