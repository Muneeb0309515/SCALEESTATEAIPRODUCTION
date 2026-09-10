-- Property, market, sales, and listing-history records retain provider context.
create table if not exists public.markets (
  id uuid primary key default gen_random_uuid(), organization_id uuid not null references public.organizations(id),
  city text, state text, zip text, median_price numeric, average_price numeric, price_per_sqft numeric,
  active_listings integer, pending_listings integer, recent_sold_count integer, days_on_market numeric,
  market_trend text check (market_trend in ('up','stable','down')), absorption_rate numeric,
  source text, confidence text, updated_at timestamptz not null default now()
);
create table if not exists public.property_sales (
  id uuid primary key default gen_random_uuid(), property_id uuid not null references public.properties(id) on delete cascade,
  sale_date date, sale_price numeric, sale_type text, source text, confidence text, recorded_at timestamptz not null default now()
);
create table if not exists public.listing_history (
  id uuid primary key default gen_random_uuid(), property_id uuid not null references public.properties(id) on delete cascade,
  listing_date date, status text, list_price numeric, days_on_market integer, source text, confidence text, recorded_at timestamptz not null default now()
);
alter table public.markets enable row level security;
create policy "members read markets" on public.markets for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
