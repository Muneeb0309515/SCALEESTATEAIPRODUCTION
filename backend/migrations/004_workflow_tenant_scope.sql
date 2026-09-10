-- Required after 001 for repository-created workflow entities.
alter table public.deals add column if not exists seller_id uuid references public.sellers(id);
alter table public.outreach add column if not exists organization_id uuid references public.organizations(id);
alter table public.buyer_distributions add column if not exists organization_id uuid references public.organizations(id);
alter table public.buyer_offers add column if not exists organization_id uuid references public.organizations(id);
alter table public.transactions add column if not exists organization_id uuid references public.organizations(id);
alter table public.outreach enable row level security;
alter table public.buyer_distributions enable row level security;
alter table public.buyer_offers enable row level security;
alter table public.transactions enable row level security;
create policy "members read outreach" on public.outreach for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
create policy "members read distributions" on public.buyer_distributions for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
create policy "members read buyer offers" on public.buyer_offers for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
create policy "members read transactions" on public.transactions for select using (organization_id in (select organization_id from public.organization_memberships where user_id=auth.uid()));
