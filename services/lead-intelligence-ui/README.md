# Lead Intelligence UI

Separate frontend prototype for the Novactiv B2B Lead Intelligence service.

The service now has a small Python backend and Supabase persistence:

- React 18 + TypeScript;
- Tailwind CSS;
- Python HTTP API;
- Supabase tables `li_*`;
- API-backed filters, sorting, search, scenarios, toast actions;
- Apify-ready scenario collector;
- JSON company import endpoint.

Planned route:

```text
http://45.92.174.232/intelligence/
```

Local development:

```bash
npm install
npm run dev
```

Server APIs:

```text
GET  /intelligence/api/bootstrap
POST /intelligence/api/scenarios/{slug}/run
POST /intelligence/api/leads/{id}/action
POST /intelligence/api/import/companies
```

Real Apify collection requires:

```text
APIFY_TOKEN=
APIFY_ACTOR_ID=
APIFY_DEFAULT_CITY=Новосибирск
APIFY_DEFAULT_LIMIT=25
```
