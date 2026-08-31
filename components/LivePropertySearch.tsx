"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";
import { ArrowRight, ChevronLeft, ChevronRight, Filter, MapPinned, Search, ShieldCheck } from "lucide-react";

function getOrganizationId(session: { user?: { app_metadata?: Record<string, unknown> } } | null) {
  const organizationId = session?.user?.app_metadata?.organization_id;
  return typeof organizationId === "string" && organizationId.length > 0 ? organizationId : null;
}

type PropertyResult = {
  provider_property_id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: string;
  list_price?: number | null;
  beds?: number | null;
  baths?: number | null;
  living_area?: number | null;
  listing_status?: string | null;
  source: string;
  data_updated_at: string;
};

export function LivePropertySearch() {
  const [location, setLocation] = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [status, setStatus] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minBeds, setMinBeds] = useState("");
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<PropertyResult[]>([]);
  const [total, setTotal] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [accessIssue, setAccessIssue] = useState<"auth" | "organization" | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [signedInEmail, setSignedInEmail] = useState<string | null>(null);

  useEffect(() => {
    const client = getSupabaseBrowserClient();
    if (!client) {
      setAuthReady(true);
      return;
    }
    const persistedSession = getPersistedSupabaseSession();
    setSignedInEmail(persistedSession?.user.email ?? null);
    const sessionCheck = client.auth.getSession().then(({ data }) => data.session).catch(() => null);
    void Promise.race([sessionCheck, new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500))]).then((session) => {
      const resolvedSession = session ?? persistedSession;
      setSignedInEmail(resolvedSession?.user.email ?? null);
      setAuthReady(true);
    });
    const { data: listener } = client.auth.onAuthStateChange((_event, session) => {
      setSignedInEmail(session?.user.email ?? null);
      setAuthReady(true);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  async function submit(event?: FormEvent, requestedPage = 1) {
    event?.preventDefault();
    setPage(requestedPage);
    if (!location.trim()) {
      setError("Enter a city, ZIP code, neighborhood, or county to search.");
      return;
    }
    setLoading(true);
    setError("");
    setAccessIssue(null);
    try {
      const client = getSupabaseBrowserClient();
      const persistedSession = getPersistedSupabaseSession();
      const session = client
        ? await Promise.race([client.auth.getSession().then(({ data }) => data.session).catch(() => null), new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500))])
        : null;
      const resolvedSession = session ?? persistedSession;
      const accessToken = resolvedSession?.access_token;
      if (!accessToken) {
        setAccessIssue("auth");
        throw new Error("Sign in to an approved workspace before searching live property records.");
      }
      const organizationId = getOrganizationId(resolvedSession);
      if (!organizationId) {
        setAccessIssue("organization");
        throw new Error("Your signed-in account is not assigned to an approved organization.");
      }
      const params = new URLSearchParams({ location: location.trim(), page: String(requestedPage), limit: "50" });
      if (propertyType) params.set("property_type", propertyType);
      if (status) params.set("status", status);
      if (maxPrice) params.set("max_price", maxPrice);
      if (minBeds) params.set("min_beds", minBeds);
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 25000);
      let response: Response;
      try {
        response = await fetch(`/api/v1/providers/property-search?${params.toString()}`, { headers: { Authorization: `Bearer ${accessToken}`, "X-Organization-Id": organizationId }, signal: controller.signal });
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") throw new Error("The property provider took too long to respond. Try a narrower location or search again.");
        throw new Error("The live property provider connection was interrupted. Search again in a moment.");
      } finally {
        window.clearTimeout(timeoutId);
      }
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const code = body?.detail?.code;
        setAccessIssue(code === "CONFIGURATION_REQUIRED" || code === "AUTHENTICATION_REQUIRED" ? "auth" : code === "ORGANIZATION_REQUIRED" || code === "ORGANIZATION_ACCESS_DENIED" ? "organization" : null);
        throw new Error(body?.detail?.message ?? "Property search is unavailable.");
      }
      setResults(body.results ?? []);
      setTotal(body.total ?? 0);
      setHasNextPage(Boolean(body.has_next_page));
    } catch (caught) {
      setResults([]);
      setTotal(0);
      setHasNextPage(false);
      setError(caught instanceof Error ? caught.message : "Property search is unavailable.");
    } finally {
      setLoading(false);
    }
  }

  function changePage(nextPage: number) {
    setPage(nextPage);
    window.setTimeout(() => void submit(undefined, nextPage), 0);
  }

  return <>
    <header className="screen-header"><div><p className="eyebrow">Property discovery</p><h1>Find the next defensible opportunity.</h1><p>Search Realtor listings through RealtyAPI.io, retain source context, and move only verified records into research.</p></div><Link href="/settings" className="button button-secondary"><ShieldCheck size={16} /> Provider status</Link></header>
    <div className="status-banner"><ShieldCheck size={18} /><p><strong>Live provider connected.</strong> RealtyAPI.io is configured server-side. {authReady ? signedInEmail ? `Authenticated as ${signedInEmail}.` : "Sign in before submitting a live search." : "Checking workspace authentication…"}</p><span>REALTYAPI.IO</span></div>
    <form className="panel filter-panel" onSubmit={submit}><div className="filter-topline"><div><span className="eyebrow">Search criteria</span><p>Search by city, ZIP, neighborhood, or county. Every result retains provider freshness.</p></div><Link href="/search" className="text-button"><Filter size={15} /> Saved criteria</Link></div><div className="filters"><label className="filter-field wide"><span>Location</span><input aria-label="Location" className="live-input" value={location} onChange={(event) => { setLocation(event.target.value); setPage(1); }} placeholder="Austin, TX or 78744" /></label><label className="filter-field"><span>Property category</span><select aria-label="Property category" className="live-input" value={propertyType} onChange={(event) => { setPropertyType(event.target.value); setPage(1); }}><option value="">All property types</option><option value="single_family">Single family</option><option value="condo">Condominium</option><option value="townhome">Townhome</option><option value="multi_family">Multi-family</option><option value="land">Land</option></select></label><label className="filter-field"><span>Listing status</span><select aria-label="Listing status" className="live-input" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">Active & pending</option><option value="for_sale">For sale</option><option value="pending">Pending</option><option value="sold">Sold</option></select></label><label className="filter-field"><span>Maximum price</span><select aria-label="Maximum price" className="live-input" value={maxPrice} onChange={(event) => { setMaxPrice(event.target.value); setPage(1); }}><option value="">Any price</option><option value="200000">$200,000</option><option value="300000">$300,000</option><option value="500000">$500,000</option><option value="750000">$750,000</option></select></label><label className="filter-field"><span>Minimum beds</span><select aria-label="Minimum beds" className="live-input" value={minBeds} onChange={(event) => { setMinBeds(event.target.value); setPage(1); }}><option value="">Any bedrooms</option><option value="2">2+ bedrooms</option><option value="3">3+ bedrooms</option><option value="4">4+ bedrooms</option></select></label></div><div className="filter-footer"><span><Filter size={14} /> RealtyAPI.io search route ready</span><button className="button button-primary" type="submit" disabled={loading}><Search size={16} /> {loading ? "Searching…" : "Search properties"}</button></div>{error && <div className="form-error" role="alert"><span>{error}</span>{accessIssue && <Link href={accessIssue === "organization" ? "/settings" : "/sign-in"} className="text-button">Review access state</Link>}</div>}</form>
    <div className="split-layout search-split"><section className="panel"><header className="panel-heading"><div><h2>Search results</h2><p>{total ? `${total.toLocaleString()} source-backed listings` : "Paginated provider results with source-bound property handoff."}</p></div></header><div className="result-toolbar"><span>{results.length ? `Page ${page}` : "Awaiting search"}</span><div><button type="button" className="view-switch active">List</button><button type="button" className="view-switch" disabled>Map</button></div></div>{results.length ? <div className="live-results">{results.map((property) => <Link className="live-result" href={`/properties/${property.provider_property_id}`} key={property.provider_property_id}><div><strong>{property.address}</strong><span>{property.city}, {property.state} {property.zip_code} · {property.property_type}</span></div><div className="result-meta"><strong>{property.list_price ? `$${property.list_price.toLocaleString()}` : "Price unavailable"}</strong><span>{property.beds ?? "—"} bd · {property.baths ?? "—"} ba · {property.living_area ? `${property.living_area.toLocaleString()} sf` : "—"}</span><span className="result-provenance">Source: {property.source} · Updated {new Date(property.data_updated_at).toLocaleDateString()}</span></div><ArrowRight size={16} /></Link>)}</div> : <div className="empty-state"><span className="empty-icon"><Search size={22} /></span><h3>{error ? "Search could not be completed" : "No source records loaded"}</h3><p>{error || "Enter a location to retrieve live Realtor listings. No property record is inferred or seeded."}</p></div>}<div className="pagination"><button className="text-button" type="button" disabled={page <= 1 || loading} onClick={() => changePage(page - 1)}><ChevronLeft size={14} /> Previous</button><span>{results.length ? `Page ${page}` : "No page selected"}</span><button className="text-button" type="button" disabled={!hasNextPage || loading} onClick={() => changePage(page + 1)}>Next <ChevronRight size={14} /></button></div></section><section className="panel"><header className="panel-heading"><div><h2>Map exploration</h2><p>Only provider coordinates are placed on the map.</p></div></header><div className="map-placeholder"><MapPinned size={32} /><strong>{results.length ? "Map handoff available" : "Map awaits a search"}</strong><p>{results.length ? "Open a property to research its verified coordinates and history." : "Search with a city or ZIP to retrieve verified coordinates."}</p></div></section></div>
    <section className="panel"><header className="panel-heading"><div><h2>Saved-search entry points</h2><p>Saved criteria remain organization-scoped and require authenticated persistence.</p></div></header><div className="saved-search-grid"><div><strong>Investment criteria fit</strong><p>Property-fit scoring uses documented deterministic inputs, not an AI estimate.</p></div><div><strong>Freshness controls</strong><p>Every result includes RealtyAPI.io provenance and retrieval time.</p></div><div><strong>Research handoff</strong><p>Open a listing by provider property id to begin property intelligence review.</p></div></div></section>
  </>;
}
