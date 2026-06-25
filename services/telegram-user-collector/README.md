# Telegram User Collector

Collects lead-like messages from Telegram channels and groups accessible to a dedicated Telegram user account.

This is not a bot collector. It uses a normal Telegram account through Telegram API credentials.

## Required Credentials

Create API credentials at:

```text
https://my.telegram.org
```

Required environment variables:

```text
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
TELEGRAM_SOURCES=channel_or_group_1,channel_or_group_2
SUPABASE_URL=http://kong:8000
SUPABASE_SERVICE_ROLE_KEY=
COLLECTOR_DRY_RUN=true
```

First login may require an interactive code. Run the collector once in an interactive shell to create the session file, then run it as a service.

## Rules

- Use a dedicated company Telegram account.
- Monitor only groups/channels the account can access normally.
- Do not bypass restrictions, private groups, or platform controls.
- Store source links and raw text for review.
- Start with `COLLECTOR_DRY_RUN=true`.

