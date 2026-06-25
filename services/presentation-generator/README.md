# Presentation Generator

Small HTTP service that turns structured property data into an animated HTML presentation.

## API

```http
POST /presentations/api/generate
Content-Type: application/json
```

Payload can be either a flat property object or `{ "property": { ... } }`.

Important fields:

- `id` / `external_id` / `wordpress_id`
- `title`
- `city`
- `address`
- `area_m2` / `area`
- `price`
- `description`
- `features`
- `photos` / `images` / `media`
- `manager`

Response:

```json
{
  "presentation_id": "abc123",
  "slug": "office-abc123",
  "url": "http://45.92.174.232/presentations/generated/office-abc123/",
  "status": "ready"
}
```

The first MVP output is HTML because it supports animation and can be shared instantly.
PDF/PPTX export can be added later from the same normalized payload.
