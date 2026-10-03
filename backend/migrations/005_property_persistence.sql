-- Phase 6 Task 2: durable, organization-scoped provider property records.
-- Apply only after 001_initial_schema.sql through 004_workflow_tenant_scope.sql
-- in the approved Supabase PostgreSQL project.

alter table public.properties add column if not exists source text;
alter table public.properties add column if not exists provider_property_id text;
alter table public.properties add column if not exists provider_listing_id text;
alter table public.properties add column if not exists list_price numeric;
alter table public.properties add column if not exists listing_url text;
alter table public.properties add column if not exists primary_photo text;
alter table public.properties add column if not exists photos jsonb not null default '[]'::jsonb;
alter table public.properties add column if not exists provenance jsonb not null default '{}'::jsonb;
alter table public.properties add column if not exists source_retrieved_at timestamptz;
alter table public.properties add column if not exists data_updated_at timestamptz;
alter table public.properties add column if not exists last_seen_at timestamptz;

create unique index if not exists properties_org_source_provider_id_idx
  on public.properties (organization_id, source, provider_property_id)
  where provider_property_id is not null;

alter table public.property_fields add column if not exists organization_id uuid references public.organizations(id);
update public.property_fields fields
set organization_id = properties.organization_id
from public.properties properties
where fields.property_id = properties.id
  and fields.organization_id is null;
alter table public.property_fields alter column organization_id set not null;
create unique index if not exists property_fields_property_field_idx
  on public.property_fields (property_id, field_name);

alter table public.properties enable row level security;
alter table public.property_fields enable row level security;

drop policy if exists "members read properties" on public.properties;
create policy "members read properties" on public.properties
  for select using (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));
drop policy if exists "members insert properties" on public.properties;
create policy "members insert properties" on public.properties
  for insert with check (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));
drop policy if exists "members update properties" on public.properties;
create policy "members update properties" on public.properties
  for update using (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  )) with check (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));

drop policy if exists "members read property fields" on public.property_fields;
create policy "members read property fields" on public.property_fields
  for select using (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));
drop policy if exists "members insert property fields" on public.property_fields;
create policy "members insert property fields" on public.property_fields
  for insert with check (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));
drop policy if exists "members update property fields" on public.property_fields;
create policy "members update property fields" on public.property_fields
  for update using (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  )) with check (organization_id in (
    select organization_id from public.organization_memberships where user_id = auth.uid()
  ));
