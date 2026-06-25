# Agent Operating System

## Purpose

This project uses agents as specialized work roles. Each agent has a narrow ownership area, required skills, and output artifacts. The coordinator integrates their work into one platform.

## Global Rules

- Do not expose secrets in logs, documentation, commits, or chat.
- Do not scrape private data, bypass authentication, or defeat source protections.
- Prefer official APIs and public sources with clear collection boundaries.
- Every lead must keep source metadata.
- Every automation must be testable before production use.
- Store permanent business data in Supabase, not in n8n execution history.
- Keep deployment repeatable through Docker Compose and migrations.
- Add backups before storing real leads.

## Agent Outputs

Each agent should produce:
- A short plan.
- Files changed.
- Commands run.
- Risks or blockers.
- Next recommended action.

## Handoff Format

Use this format when one agent hands work to another:

```text
Context:
Decision:
Files:
Commands:
Risks:
Next:
```

## Definition of Done

A task is done when:
- The change is documented.
- Required files are present.
- The behavior can be verified.
- Risks are called out.
- The next agent can continue without guessing.

