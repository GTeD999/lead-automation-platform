# Services

Application services will live here.

Planned services:
- `lead-collector`: source-specific collectors and ingestion.
- `normalizer`: contact cleanup, deduplication, scoring, and classification helpers.
- `presentation-generator`: future PDF/PPTX generation for properties.

Each service should expose:
- Clear configuration through environment variables.
- Healthcheck command.
- Structured logs.
- Test payload examples.

