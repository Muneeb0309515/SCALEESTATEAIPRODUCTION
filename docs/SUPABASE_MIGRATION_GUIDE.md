# SCALEESTATE AI — Supabase Migration Guide

## Important target check

Apply these migrations only in the approved Supabase PostgreSQL project whose URL matches the project’s configured `NEXT_PUBLIC_SUPABASE_URL` and server-side `SUPABASE_URL`. Do not run them in the legacy managed database connected to the project SQL tool; that database is not the approved Supabase PostgreSQL target and previously reported `public.organizations` as missing.

Before running SQL, confirm the Supabase Dashboard project reference in **Project Settings → General** matches the hostname in the configured Supabase URL. Do not paste any API key into SQL Editor or into this guide.

## Apply the migrations

Open **Supabase Dashboard → the approved project → SQL Editor → New query**. Copy and run each attached file separately, in this exact order:

1. `001_initial_schema.sql` — core users, organizations, memberships, properties, workflows, RLS, and immutable audit trigger.
2. `002_workflow_support.sql` — saved searches, plans, subscriptions, AI drafts, document access logs, and related RLS policies.
3. `003_property_intelligence.sql` — property-intelligence tables.
4. `004_workflow_tenant_scope.sql` — remaining organization-scope columns and policies.

Wait for a successful result after each file. If a file fails, stop and save the exact error text; do not rerun later files because they may depend on the failed migration. The scripts are designed with `if not exists` guards for the main objects, but a partially applied script should still be reviewed before retrying.

## Verify the schema

After all four files succeed, run this verification query in a new SQL Editor query:

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in ('users', 'organizations', 'organization_memberships', 'properties', 'saved_searches', 'ai_drafts')
order by table_name;
```

The result should contain all six table names. Then verify row-level security and the immutable audit trigger:

```sql
select tablename, rowsecurity
from pg_tables
where schemaname = 'public'
  and tablename in ('organizations', 'properties', 'deals', 'buyers', 'documents', 'audit_logs')
order by tablename;

select tgname
from pg_trigger
where tgrelid = 'public.audit_logs'::regclass
  and not tgisinternal;
```

Do not insert sample properties, owners, sellers, or financial records. SCALEESTATE AI must display only provider-backed or user-created records with provenance.

## Create or assign the first organization

The signed-in user must exist in `public.users` and must have a row in `public.organization_memberships`. Use the authenticated user UUID from **Supabase Dashboard → Authentication → Users**. If the user row is absent, create only the identity mirror for that real Auth user, then create one organization and membership. Replace the placeholders locally in SQL Editor; do not send UUIDs or private data in chat.

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

The frontend reads `organization_id` from the signed-in user’s Supabase `app_metadata`. The organization UUID must therefore be assigned to the user’s Auth app metadata through the approved administrative process. Do not place an organization UUID in frontend source code or use `user_metadata` as an authorization source.

## Finish live-search verification

Restart or refresh the SCALEESTATE AI preview, open `/sign-in`, and sign in with the Auth user that belongs to the organization. Search for a city or ZIP, select a property category, and submit. The browser request must contain both `Authorization: Bearer <session-token>` and `X-Organization-Id: <organization-uuid>`. The backend verifies the JWT, verifies organization membership, then calls RealtyAPI.io. Results must retain `source: realtyapi`, `data_updated_at`, and `provider_property_id`.

If the UI reports that the account is not assigned to an organization, stop and correct the Auth app metadata and membership row. If it reports organization access denied, verify the membership row for the exact Auth user UUID. Never bypass these checks to make the search appear to work.
