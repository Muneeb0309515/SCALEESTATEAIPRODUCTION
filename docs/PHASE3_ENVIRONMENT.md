# Phase 3 Environment Readiness Contract

This document records variable names and usage only. It contains no values, credentials, tokens, or connection strings.

## RealtyAPI

| Variable | Required? | Used by | Expected format | Visibility |
|---|---|---|---|---|
| `PROPERTY_DATA_PROVIDER` | Required for the RealtyAPI path | Backend provider registry and availability guard | Exact value `realtyapi` | Server-only |
| `REALTYAPI_API_KEY` | Required | Backend RealtyAPI adapter request header | Provider-issued non-empty secret string | Server-only; never expose to client |
| `REALTYAPI_BASE_URL` | Required by the live readiness guard and adapter | Backend RealtyAPI adapter | HTTPS base URL, without embedded credentials | Server-only |

The readiness result is `REALTYAPI_CONFIGURED` only when all three conditions are satisfied. Otherwise it is `REALTYAPI_NOT_CONFIGURED`.

## Supabase backend and authentication

| Variable | Required? | Used by | Expected format | Visibility |
|---|---|---|---|---|
| `SUPABASE_URL` | Required for backend persistence and JWT issuer construction | Backend settings, repository, authentication | HTTPS Supabase project URL; `/rest/v1` suffix is tolerated and removed for issuer use | Server-only |
| `SUPABASE_KEY` | Required for backend repository membership/RLS operations | Backend Supabase client | Supabase server/API key secret string | Server-only; never expose to client |
| `SUPABASE_PROJECT_VALIDATED` | Required for production readiness gate | Backend configuration guard | Exact value `true` after the approved project has been validated | Server-only; not secret |
| `SUPABASE_JWKS_JSON` | Optional override | Backend JWT verification | HTTPS JWKS URL; otherwise the project issuer JWKS URL is used | Server-only |

The readiness result is `SUPABASE_CONFIGURED` only when the project URL is valid, a backend key is present, and `SUPABASE_PROJECT_VALIDATED=true`. Otherwise it is `SUPABASE_NOT_CONFIGURED`.

## Supabase browser client

| Variable | Required? | Used by | Expected format | Visibility |
|---|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Required for browser auth/session client | Next.js browser Supabase client | HTTPS Supabase project URL | Client-visible; never treat as a secret |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Required for browser auth/session client | Next.js browser Supabase client | Supabase public anon key | Client-visible by Supabase design; still do not log unnecessarily |

The browser client is not an authorization boundary. The backend validates the bearer token and organization membership, and database RLS remains authoritative.

## Other server integrations (not required for the RealtyAPI/Supabase readiness check)

| Variable | Required? | Used by | Expected format | Visibility |
|---|---|---|---|---|
| `BUILT_IN_FORGE_API_URL` | Optional for document storage/managed services | Backend document storage and server helper integrations | HTTPS service URL | Server-only |
| `BUILT_IN_FORGE_API_KEY` | Optional for document storage/managed services | Backend document storage and server helper integrations | Secret API key | Server-only |
| `DOCUMENT_BUCKET` | Optional for document storage | Backend document storage | Bucket name | Server-only |

## Safe check

The backend exposes `GET /api/v1/integrations/readiness` and includes the same status values in `GET /health`. Responses contain only the following status strings:

```json
{
  "realtyapi": "REALTYAPI_NOT_CONFIGURED",
  "supabase": "SUPABASE_NOT_CONFIGURED"
}
```

The check does not return key presence details, key prefixes, JWT contents, passwords, tokens, or connection strings. It does not make external provider calls. Live validation must remain a separate, small, explicitly authorized test after readiness is `CONFIGURED`.

## Current Phase 3 state

At the time of this implementation, no approved live values were available in the sandbox. The safe check therefore must be reported as not configured unless the runtime environment is later populated through the approved configuration path. No `.env` file is created or committed.
