# SCALEESTATE AI — Supabase Migration and Safety Guide

## Scope and target verification

Run migrations only in the approved direct Supabase PostgreSQL project whose URL matches the project's configured `NEXT_PUBLIC_SUPABASE_URL` and server-side `SUPABASE_URL`. Do not run them in the legacy managed database connected to the project SQL tool; that database is not the approved Supabase target and has previously reported `public.organizations` as missing.

Before any SQL execution, confirm the Supabase Dashboard project reference in **Project Settings → General** matches the hostname in the configured Supabase URL. Never paste an API key into SQL Editor or into this guide.

**Start with read-only inspection.** Review the actual schema, all policies, constraints, indexes, data consistency, and the migration ledger for the exact project. A file's presence in the repository or a migration's name in a remote ledger is not sufficient evidence that its SQL ran as expected. Never reset the database, delete migration history, or replay a migration simply because the ledger and repository names differ.

## Fresh installation

For a clean installation, apply the baseline migrations **001–005 in order**, then apply the new tenant-isolation hardening migration **006** before allowing authenticated property-field access. Run each file separately in **Supabase Dashboard → the approved project → SQL Editor → New query**:

1. `001_initial_schema.sql` — core identity, organization, property, workflow, RLS, and immutable audit artifacts.
2. `002_workflow_support.sql` — saved searches, subscriptions, AI drafts, document access logs, and related RLS policies.
3. `003_property_intelligence.sql` — market, property-sales, and listing-history tables.
4. `004_workflow_tenant_scope.sql` — remaining workflow organization-scope columns and policies.
5. `005_property_persistence.sql` — provider-backed property columns, provider-identity and property-field unique indexes, field organization scope, backfill, and persistence policies.
6. `006_property_fields_tenant_isolation.sql` — tenant-aware composite foreign key and the complete authenticated-only property-field policy set.

Wait for a successful result after each file. If one fails, stop and investigate the schema and exact error before proceeding; do not skip it or blindly rerun a partly applied file. Migration 006 deliberately aborts before DDL if an existing field-to-property organization mismatch is found. It does not silently move or delete property data.

After migrations succeed, inspect the schema and policies with read-only queries such as:

```sql
select table_name, column_name, is_nullable, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name in ('properties', 'property_fields')
order by table_name, ordinal_position
limit 100;

select schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public'
  and tablename in ('properties', 'property_fields')
order by tablename, policyname
limit 100;

select c.conrelid::regclass::text as table_name,
       c.conname as constraint_name,
       pg_get_constraintdef(c.oid) as definition
from pg_constraint c
where c.conrelid in ('public.properties'::regclass, 'public.property_fields'::regclass)
order by table_name, constraint_name
limit 100;
```

The field table should have one authenticated policy each for SELECT, INSERT, UPDATE, and DELETE; the policy list must contain no superseded permissive field policies. The composite constraint must relate `(property_id, organization_id)` to `(properties.id, properties.organization_id)`.

Run the RLS integration script only on a **disposable Supabase-compatible test database**, after migrations 001–006:

```bash
psql "$SUPABASE_TEST_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f backend/tests/rls_property_fields.sql
```

The script uses `authenticated` and `anon` database roles with JWT request claims, verifies tenant-crossing inserts and reads/writes are rejected, checks same-organization CRUD, and rolls back its fixtures and temporary grants. Do not point it at a production database.

## Already-provisioned database

Do not apply the clean-install sequence to an existing project. First record the result of read-only checks for the exact project reference:

1. Read the remote Supabase migration ledger.
2. Read actual columns, RLS status, every policy on `properties` and `property_fields`, all foreign keys/unique indexes, and mismatch counts.
3. Compare those results with the repository SQL; do not infer that a migration ran from its filename alone.
4. If schema or policy state differs from expectations, stop and prepare a separately reviewed reconciliation plan. Do not edit or delete ledger rows to make history appear consistent.

### Read-only assessment for the active SCALEESTATE AI project

On **2026-10-12**, read-only inspection of the active project (`koahlsjoukfoxmfrcvwb`) established the following:

- The remote migration ledger contains version `20261003081716`, named `phase6_property_persistence`.
- The `properties` table has the provider-persistence columns from local migration 005, including source/provider IDs, list price, listing and photo fields, provenance, and retrieval timestamps. Its unique provider-identity index `properties_org_source_provider_id_idx` is present.
- `property_fields.organization_id` is present and non-null. The organization foreign key, property foreign key, and unique `(property_id, field_name)` index from migration 005 are present. An aggregate read found zero `property_fields` rows and zero organization/property mismatches at inspection time.
- Both tables have RLS enabled. `properties` has its expected member SELECT/INSERT/UPDATE policies. `property_fields` had the three member policies plus two additional **PERMISSIVE** policies named `property_fields_select` and `property_fields_insert`. PostgreSQL ORs permissive policies together; creating another narrow policy would not supersede those older policies.
- The active database did **not** have a composite `(property_id, organization_id)` foreign key.

This evidence maps `phase6_property_persistence` to the actual schema effects of local migration 005: its provider columns, indexes, field organization column/backfill, and persistence policies are present. It does **not** make migration 005 safe to replay. **Do not rerun migration 005 on this project.**

The other remote ledger entries observed were `enable_rls_on_all_disabled_tables` (`20260916035408`), `complete_org_scoped_rls_policies` (`20260916035755`), and `fix_membership_rls_recursion` (`20261007121948`). They do not have one-to-one SQL files with those names in this repository; their exact SQL history must not be guessed from local migrations 001–004.

Local migration 006 is a forward-only reconciliation for the identified tenant-isolation gap. It checks existing links before DDL, adds the referenced composite unique key and composite FK, then removes every existing `property_fields` policy and installs exactly four authenticated member policies. It preserves field data and refuses to silently repair inconsistent rows. **Migration 006 was not applied to the active project during this task.** Apply it only through a separately reviewed, approved change process, after a backup/staging rehearsal and another read-only consistency check. This guide is not authorization to change production.

If the migration's preflight reports mismatched records, stop. Review the affected records and decide on a separately reviewed data-reconciliation plan; do not disable RLS or weaken constraints to force the migration through.

## First organization setup

The signed-in user must exist in `public.users` and have a row in `public.organization_memberships`. Use the Auth user UUID from **Supabase Dashboard → Authentication → Users**. If the identity mirror is absent, create only the mirror for that real Auth user, then create one organization and membership. Replace placeholders locally in SQL Editor; never send UUIDs or private data in chat.

```sql
insert into public.users (id, email)
select id, email
from auth.users
where id = '<AUTH_USER_UUID>'
on conflict (id) do update set email = excluded.email;

insert into public.organizations (name, tier)
values ('<YOUR ORGANIZATION NAME>', 'starter')
returning id;
```

Copy the returned organization UUID and run:

```sql
insert into public.organization_memberships (organization_id, user_id, role)
values ('<ORGANIZATION_UUID>', '<AUTH_USER_UUID>', 'admin')
on conflict (organization_id, user_id) do update set role = excluded.role;
```

The frontend reads `organization_id` from the signed-in user's Supabase `app_metadata`. Assign the organization UUID through the approved administrative process. Do not put an organization UUID in frontend source code or use `user_metadata` as an authorization source.

## Finish live-search verification

Restart or refresh the SCALEESTATE AI preview, open `/sign-in`, and sign in with the Auth user assigned to the organization. Search for a city or ZIP, select a property category, and submit. The browser request must include `Authorization: Bearer <session-token>` and `X-Organization-Id: <organization-uuid>`. The backend verifies the JWT and organization membership before calling RealtyAPI.io. Results should retain `source: realtyapi`, `data_updated_at` when supplied, and `provider_property_id`.

If the UI reports that the account is not assigned to an organization, stop and correct the Auth app metadata and membership row. If it reports organization access denied, verify the membership for the exact Auth user UUID. Never bypass these checks to make a search appear to work.
