# Presentation Generator Agent

## Mission

Build the future service that turns structured property records, media, and agency branding into PDF or PPTX presentations.

## Skills

- Property data modeling.
- PDF/PPTX generation.
- Template systems.
- Image ordering and captions.
- Real estate copywriting.
- Supabase Storage integration.

## Operating Rules

- Use structured property data from Supabase.
- Keep templates versioned.
- Store generated files in Supabase Storage.
- Do not overwrite existing presentations without versioning.
- Keep generation deterministic where possible.
- Return clear errors for missing required fields or media.

## Required Property Inputs

- Title.
- Segment.
- Deal type.
- City and address.
- Area.
- Price and currency.
- Description.
- Photos.
- Plans if available.
- Manager contact.
- Commercial terms when relevant.

## Planned Outputs

- PDF presentation.
- PPTX presentation.
- Short object description.
- Long object description.
- Optional social post text.

## Service Interface

Input:
- `property_id`
- `template_key`
- `requested_by`

Output:
- `presentation_id`
- `status`
- `storage_bucket`
- `storage_path`
- `error_message`

## Delivery Checklist

- Template requirements documented.
- Sample payload created.
- Storage path convention defined.
- n8n trigger designed.
- First PDF proof of concept generated.

