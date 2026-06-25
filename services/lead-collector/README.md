# Lead Collector

Conservative lead collection service skeleton.

Current scope:
- Extract contact candidates from text.
- Normalize Russian phone numbers.
- Normalize email, Telegram username, and VK links.
- Emit source metadata compatible with Supabase.
- Run in dry-run mode by default.

No network collectors are enabled yet. Source-specific collectors should be added only after the source access method, rules, rate limits, and dry-run output are documented.

## Example

```bash
python3 services/lead-collector/src/lead_collector.py \
  --source-type manual \
  --source-name test \
  --source-url https://example.com/post/1 \
  --text "Office for rent, call +7 913 123-45-67, telegram @manager"
```
