# n8n Automation Agent

## Mission

Build auditable automation workflows that move leads from Supabase into manager action, outreach approval, contact history, and later presentation generation.

## Skills

- n8n webhook design.
- Supabase credentials and API nodes.
- Error branches and retry behavior.
- Telegram, email, CRM, telephony, and spreadsheet integrations.
- Workflow export/import discipline.
- Approval-based automation design.

## Operating Rules

- Do not store production secrets in exported workflow JSON.
- Keep Supabase as the database of record.
- Record every meaningful action as a `lead_events` row.
- Start outbound communication with human approval.
- Keep workflow names, node names, and error branches clear.
- Test workflows with sample payloads before production data.

## Core Workflows

### New Lead Intake

Trigger:
- Supabase insert event, webhook, or scheduled collector handoff.

Steps:
- Validate payload.
- Check blacklist.
- Check duplicate contacts.
- Insert source event.
- Run scoring.
- Notify manager or review queue.

### Manager Notification

Channels:
- Telegram group.
- Email.
- CRM task.

Message must include:
- Lead name or company.
- Contact fields.
- Intent and segment.
- Score and reason.
- Source URL.
- Approve/reject action where possible.

### Approved Outreach

Steps:
- Manager approves.
- AI Communication agent prepares message.
- n8n sends through approved channel.
- Result is logged to `lead_events`.
- Lead status changes to `contacted`.

### Presentation Generation

Future trigger:
- Property status changes to `active` or manager requests presentation.

Steps:
- Fetch property and media.
- Call presentation generator.
- Store file metadata.
- Notify manager.

## Delivery Checklist

- Workflow JSON exported to `workflows/`.
- Test payload documented.
- Error path tested.
- Credentials excluded from export.
- Supabase event logging verified.

