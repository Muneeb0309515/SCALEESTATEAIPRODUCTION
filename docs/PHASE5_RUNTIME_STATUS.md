# SCALEESTATE AI Phase 5 Runtime Status

**Phase:** Runnable web runtime and deployment readiness  
**Application:** Existing SCALEESTATE AI Next.js + FastAPI application  
**RapidAPI:** Not implemented  
**Live property data:** Not fabricated or substituted  
**Credentials:** None exposed or stored

## Runtime status

**PASS — the application is running in the available runtime.**

The existing development command was used:

```bash
pnpm dev
```

The runtime starts:

- Next.js on port `3000`;
- FastAPI/Uvicorn on port `8000`;
- Next.js rewrites `/api/*` and `/health` to FastAPI.

### Genuine runtime issue fixed

The first runtime attempt started Next.js but FastAPI exited because the sandbox system Python did not contain the repository-declared backend packages, including `pydantic-settings`, Supabase, and PyJWT.

The existing Dockerfile already installs `backend/requirements.txt` correctly for deployment. To make the local runtime robust without changing application behavior, the runtime scripts now support an optional interpreter selector:

```text
PYTHON_BIN
```

Both `infra/dev.mjs` and `infra/prod.mjs` preserve `python3` as the default and use `PYTHON_BIN` only when supplied. The verified runtime used the existing disposable Python environment containing the declared dependencies:

```bash
PYTHON_BIN=/tmp/scaleestate-phase1-venv/bin/python pnpm dev
```

No provider, authentication, normalization, database, or frontend behavior was changed.

## URL

The application is available locally at:

- [http://localhost:3000](http://localhost:3000)

The sandbox public URL was also verified:

- [https://3000-izzooaiwi83hfmx2g8nen-5d09dca6.us4.manus.computer](https://3000-izzooaiwi83hfmx2g8nen-5d09dca6.us4.manus.computer)

The public `/dashboard` route returned HTTP 200.

## Runtime route verification

| Route | Result |
|---|---:|
| `/` | HTTP 307 redirect to `/dashboard` |
| `/dashboard` | HTTP 200 |
| `/search` | HTTP 200 |
| `/properties` | HTTP 200 |
| `/deals` | HTTP 200 |
| `/sellers` | HTTP 200 |
| `/buyers` | HTTP 200 |
| `/contracts` | HTTP 200 |
| `/settings` | HTTP 200 |
| `/sign-in` | HTTP 200 |

## API/runtime verification

### Health and readiness

`GET /health` returned HTTP 200 with safe status-only output:

```json
{
  "status": "ready",
  "mode": "configuration_required",
  "services": {
    "realtyapi": "REALTYAPI_NOT_CONFIGURED",
    "supabase": "SUPABASE_NOT_CONFIGURED"
  }
}
```

`GET /api/v1/integrations/readiness` returned HTTP 200 with safe configuration statuses. No secret values, key prefixes, tokens, or connection strings were returned.

### Protected routes

Unauthenticated requests to:

- `/api/v1/providers/property-search?location=Travis%20County%2C%20TX`
- `/api/v1/properties`

were rejected with HTTP 503 and the existing safe configuration/authentication boundary. No property records were returned.

## Build and tests

| Check | Result |
|---|---|
| `pnpm check` | **PASS** |
| `pnpm build` | **PASS** |
| `pnpm exec vitest run tests/architecture.test.ts` | **PASS — 6 tests** |
| `PYTHONPATH=. /tmp/scaleestate-phase1-venv/bin/python -m pytest -q backend/tests` | **PASS — 61 tests, 12 subtests** |
| Runtime route checks | **PASS** |
| Health/readiness checks | **PASS** |
| Protected-route checks | **PASS** |

The backend suite reported one existing deprecation warning from Starlette/AnyIO; no test failed.

## Deployment configuration

The existing production configuration remains in place:

- `Dockerfile` installs Node, Python, the declared backend requirements, builds Next.js, and starts `infra/prod.mjs`.
- `infra/prod.mjs` proxies the public port to Next.js and routes `/api/*` and `/health` to FastAPI.
- `PYTHON_BIN` is optional. Production containers may continue using the default `python3` because the Dockerfile installs the requirements into that interpreter.
- No `.env` file, secret, API key, token, or credential was added.

## Required environment variables for live functionality

### RealtyAPI server-side

```text
PROPERTY_DATA_PROVIDER=realtyapi
REALTYAPI_API_KEY=<server-side secret>
REALTYAPI_BASE_URL=<approved HTTPS base URL>
```

### Supabase server-side

```text
SUPABASE_URL=<server-side project URL>
SUPABASE_KEY=<server-side service/API key>
SUPABASE_PROJECT_VALIDATED=true
```

Optional server-side override:

```text
SUPABASE_JWKS_JSON=<approved JWKS configuration>
```

### Supabase browser client

```text
NEXT_PUBLIC_SUPABASE_URL=<browser-safe project URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<browser-safe anon key>
```

Optional existing managed integrations remain documented separately, including document storage variables. Only variables required by enabled deployment features should be configured.

## Remaining environment blockers

The application is runnable in safe preview mode, but live functionality remains blocked because every approved live variable is currently absent:

- `PROPERTY_DATA_PROVIDER`
- `REALTYAPI_API_KEY`
- `REALTYAPI_BASE_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_PROJECT_VALIDATED`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

The runtime correctly reports these integrations as not configured and does not fabricate fallback data.

## Exact next action for live validation

Configure the listed RealtyAPI and Supabase variables through the approved deployment/secrets mechanism, without placing values in source code, commits, ZIP files, browser bundles, documentation, or chat.

Then run the previously authorized Phase 3.1 validation only:

1. RealtyAPI `/autocomplete`, if required.
2. Small Travis County `/search/bylocation` request.
3. Texas/county validation of returned records.
4. One `/details/byid` attempt using a returned valid provider ID.
5. Smallest practical pagination check.
6. Repeat for Bexar County.
7. Validate malformed, empty, and provider-error handling.
8. Validate canonical normalization and provenance retention.
9. Run the relevant regression tests.

RapidAPI must remain deferred.
