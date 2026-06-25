# Telegram Collector Setup

## Approach

The collector uses a normal Telegram user account, not a bot. This is required for groups where a bot cannot be added.

The account can only read groups/channels it can access normally. It cannot see private data, hidden phone numbers, or messages from groups it has not joined.

## What It Collects

- Message text.
- Public message link when available.
- Phone/email/Telegram/VK contacts written in the message.
- Real estate intent signals such as buy, sell, rent, lease out, invest.
- Segment signals: commercial, residential, mixed.

## What It Cannot Collect

- Hidden Telegram phone numbers.
- Closed/private groups without account access.
- Messages from groups where the account is not a member.
- Data behind access controls.

## Required Inputs

Create credentials at `https://my.telegram.org`:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_PHONE
TELEGRAM_SOURCES
```

`TELEGRAM_SOURCES` is a comma-separated list:

```text
commercial_realty_group,https://t.me/some_channel,@some_group
```

## First Run

The first run must be interactive because Telegram sends a login code.

After the session file is created, the collector can run unattended.

Start with:

```text
COLLECTOR_DRY_RUN=true
```

Switch to database writes only after dry-run output looks correct:

```text
COLLECTOR_DRY_RUN=false
```

