-- Additional approved PostgreSQL/Supabase workflow artifacts. Apply after 001 only
-- to a validated direct Supabase project.
create table if not exists public.saved_searches (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id),
  user_id uuid references public.users(id),
  name text not null,
  filters jsonb not null,
  cache_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.subscription_plans (
  id text primary key,
  display_name text not null,
  monthly_price numeric not null,
  search_limit integer not null,
  analysis_limit integer not null,
  included_members integer,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
create table if not exists public.organization_subscriptions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references public.organizations(id),
  plan_id text not null references public.subscription_plans(id),
  status text not null check (status in ('inactive','trial','active','past_due','canceled')),
  provider_customer_id text,
  provider_subscription_id text,
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.ai_drafts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id),
  seller_id uuid references public.sellers(id),
  property_id uuid references public.properties(id),
  draft_type text not null check (draft_type in ('seller_outreach','research_summary')),
  prompt_context jsonb not null,
  generated_content text not null,
  label text not null default 'AI-generated draft — user review required',
  status text not null default 'draft' check (status in ('draft','approved','edited','rejected')),
  generated_by uuid references public.users(id),
  reviewed_by uuid references public.users(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);
create table if not exists public.document_access_log (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id),
  document_id uuid not null references public.documents(id),
  user_id uuid references public.users(id),
  action text not null check (action in ('uploaded','viewed','downloaded','version_created','access_denied')),
  created_at timestamptz not null default now()
);
alter table public.saved_searches enable row level security;
alter table public.ai_drafts enable row level security;
alter table public.organization_subscriptions enable row level security;
create policy "members read saved searches" on public.saved_searches for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
create policy "members read AI drafts" on public.ai_drafts for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
create policy "members read subscription" on public.organization_subscriptions for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
