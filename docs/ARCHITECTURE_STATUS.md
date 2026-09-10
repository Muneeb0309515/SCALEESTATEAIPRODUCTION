# SCALEESTATE AI Architecture Status

## Canonical target

The approved production target for Phase 1 is:

```text
Next.js frontend
    ↓
FastAPI backend
    ↓
Supabase/PostgreSQL
    ↓
External property providers
    ↓
Deterministic real-estate engines
```

This decision preserves the existing provider adapters and deterministic Python engines and matches the active root `app/`, `components/`, `backend/`, and `backend/migrations/` implementation direction.

The production build verified the active Next route set:

```text
/
/[workspace]
/deals/[dealId]
/properties/[propertyId]
/sign-in
```

The root page redirects to `/search` at runtime. The build completed successfully with Next 16.3.3 and TypeScript checking enabled.

## Legacy path status

The archive also contains a tRPC/Drizzle/Manus-OAuth path under `server/`, `drizzle.config.ts`, `client/src/`, and related framework files. Phase 1 does not delete or modify this path. Static inspection found that the package manifest and TypeScript configuration are inconsistent with the Wouter/Vite-era client files, while the root `app/` and `components/` files are included by the Next-oriented `tsconfig.json`.

The legacy path is therefore classified as **UNRESOLVED / DO NOT DELETE YET**. The production build proves that the Next application can compile without the legacy path being part of the active TypeScript program, but it does not by itself prove that the legacy files are unreachable from every deployment or development command. The required next verification is:

1. Trace imports from the active Next entry points.
2. Inspect `infra/dev.mjs`, `infra/prod.mjs`, Docker, and deployment metadata.
3. Compare the active deployment command with the archived Vite/tRPC command path.
4. Confirm whether `server/`, `client/src/`, and Drizzle files are reachable at runtime or only retained historical code.
5. Isolate unused files in a separately documented change only after the preceding checks pass.

## Environment and external validation status

The disposable test environment had no project credentials configured. `PROPERTY_DATA_PROVIDER`, RealtyAPI credentials, Supabase browser configuration, JWKS configuration, and the validation flag were all unset. Therefore no live RealtyAPI request or Supabase request was attempted, and no credential was exposed or fabricated.

The frontend tests that require those values are correctly classified as **BLOCKED BY MISSING APPROVED ENVIRONMENT**, not as code failures.

## Benchmark architecture

Phase 1 adds `backend/app/benchmarks/` as a validation-layer contract. It extends the existing `CanonicalProperty` model rather than creating a second property entity. The benchmark layer adds county membership, field-level provenance, evidence-backed signals, and separate calculated/unknown score values. The manifest accepts exactly two distinct counties and normalizes state/county identifiers, while remaining usable for other states later.
