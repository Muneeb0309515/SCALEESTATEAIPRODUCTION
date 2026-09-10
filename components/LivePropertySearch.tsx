"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
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
  const [minBaths, setMinBaths] = useState("");
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<PropertyResult[]>([]);
  const [total, setTotal] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [accessIssue, setAccessIssue] = useState<"auth" | "organization" | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [signedInEmail, setSignedInEmail] = useState<string | null>(null);
  const resumedSearch = useRef(false);
  const shouldResumeSearch = useRef(false);
  const searchRequestInFlight = useRef(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    shouldResumeSearch.current = params.get("resume") === "1";
    if (shouldResumeSearch.current) {
      params.delete("resume");
      const cleanQuery = params.toString();
      window.history.replaceState(null, "", cleanQuery ? `${window.location.pathname}?${cleanQuery}` : window.location.pathname);
    }
    const restoredLocation = params.get("location");
    if (restoredLocation) setLocation(restoredLocation);
    setPropertyType(params.get("property_type") ?? "");
    setStatus(params.get("status") ?? "");
    setMaxPrice(params.get("max_price") ?? "");
    setMinBeds(params.get("min_beds") ?? "");
    setMinBaths(params.get("min_baths") ?? "");
    const restoredPage = Number(params.get("page") ?? "1");
    if (Number.isInteger(restoredPage) && restoredPage > 0) setPage(restoredPage);
  }, []);

  useEffect(() => {
    let active = true;
    let unsubscribe: () => void = () => {};
    const finishAuthCheck = (session: Awaited<ReturnType<NonNullable<ReturnType<typeof getSupabaseBrowserClient>>["auth"]["getSession"]>>["data"]["session"] | null) => {
      if (!active) return;
      const persistedSession = getPersistedSupabaseSession();
      const resolvedSession = session ?? persistedSession;
      setSignedInEmail(resolvedSession?.user.email ?? null);
      setAuthReady(true);
    };
    const fallbackTimer = window.setTimeout(() => finishAuthCheck(null), 1600);
    try {
      const client = getSupabaseBrowserClient();
      const persistedSession = getPersistedSupabaseSession();
      setSignedInEmail(persistedSession?.user.email ?? null);
      if (!client) {
        finishAuthCheck(null);
        return () => { active = false; window.clearTimeout(fallbackTimer); };
      }
      void client.auth.getSession().then(({ data }) => finishAuthCheck(data.session)).catch(() => finishAuthCheck(null));
      const { data: listener } = client.auth.onAuthStateChange((_event, session) => finishAuthCheck(session));
      unsubscribe = () => listener.subscription.unsubscribe();
    } catch {
      finishAuthCheck(null);
    }
    return () => { active = false; window.clearTimeout(fallbackTimer); unsubscribe(); };
  }, []);

  useEffect(() => {
    if (!authReady || !signedInEmail || !location.trim() || !shouldResumeSearch.current || resumedSearch.current) return;
    resumedSearch.current = true;
    const restoredPage = Number(new URLSearchParams(window.location.search).get("page") ?? "1");
    void submit(undefined, Number.isInteger(restoredPage) && restoredPage > 0 ? restoredPage : 1);
  }, [authReady, signedInEmail, location]);

  async function submit(event?: FormEvent, requestedPage = 1) {
    event?.preventDefault();
    event?.stopPropagation();
    if (searchRequestInFlight.current) return;
    searchRequestInFlight.current = true;
    setPage(requestedPage);
    if (!location.trim()) {
      setError("Enter a city, ZIP code, neighborhood, or county to search.");
      searchRequestInFlight.current = false;
      setLoading(false);
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
      setSignedInEmail(resolvedSession?.user.email ?? null);
      setAuthReady(true);
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
      if (minBaths) params.set("min_baths", minBaths);
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
      searchRequestInFlight.current = false;
      setLoading(false);
    }
  }

  function changePage(nextPage: number) {
    setPage(nextPage);
    window.setTimeout(() => void submit(undefined, nextPage), 0);
  }

  function buildSearchReturnPath() {
    const params = new URLSearchParams();
    if (location.trim()) params.set("location", location.trim());
    if (propertyType) params.set("property_type", propertyType);
    if (status) params.set("status", status);
    if (maxPrice) params.set("max_price", maxPrice);
    if (minBeds) params.set("min_beds", minBeds);
    if (minBaths) params.set("min_baths", minBaths);
    if (page > 1) params.set("page", String(page));
    const query = params.toString();
    const resumedQuery = query ? `${query}&resume=1` : "resume=1";
    return `/search?${resumedQuery}`;
  }

  const signInHref = `/sign-in?next=${encodeURIComponent(buildSearchReturnPath())}`;

  return <>
    <header className="screen-header"><div><p className="eyebrow">Property discovery</p><h1>Find the next defensible opportunity.</h1><p>Search Realtor listings through RealtyAPI.io, retain source context, and move only verified records into research.</p></div><Link href="/settings" className="button button-secondary"><ShieldCheck size={16} /> Provider status</Link></header>
    <div className="status-banner critical"><ShieldCheck size={18} /><p><strong>Development preview.</strong> Live RealtyAPI access is server-side and requires configured runtime credentials. This interface does not claim live validation. {authReady ? signedInEmail ? `Authenticated as ${signedInEmail}; live results remain subject to provider readiness.` : "Sign in before submitting a live search." : "Checking workspace authentication…"}</p><span>PREVIEW · NOT VALIDATED</span></div>
    <form className="panel filter-panel" onSubmit={submit}><div className="filter-topline"><div><span className="eyebrow">Search criteria</span><p>Search by city, ZIP, neighborhood, or county. Every result retains provider freshness.</p></div><Link href="/search" className="text-button"><Filter size={15} /> Saved criteria</Link></div><div className="filters"><label className="filter-field wide"><span>Location</span><input aria-label="Location" className="live-input" value={location} onChange={(event) => { setLocation(event.target.value); setPage(1); }} placeholder="Austin, TX or 78744" /></label><label className="filter-field"><span>Property category</span><select aria-label="Property category" className="live-input" value={propertyType} onChange={(event) => { setPropertyType(event.target.value); setPage(1); }}><option value="">All property types</option><option value="single_family">Single family</option><option value="condo">Condominium</option><option value="townhome">Townhome</option><option value="multi_family">Multi-family</option><option value="land">Land</option></select></label><label className="filter-field"><span>Listing status</span><select aria-label="Listing status" className="live-input" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">Active & pending</option><option value="for_sale">For sale</option><option value="pending">Pending</option><option value="sold">Sold</option></select></label><label className="filter-field"><span>Maximum price</span><select aria-label="Maximum price" className="live-input" value={maxPrice} onChange={(event) => { setMaxPrice(event.target.value); setPage(1); }}><option value="">Any price</option><option value="200000">$200,000</option><option value="300000">$300,000</option><option value="500000">$500,000</option><option value="750000">$750,000</option></select></label><label className="filter-field"><span>Minimum beds</span><select aria-label="Minimum beds" className="live-input" value={minBeds} onChange={(event) => { setMinBeds(event.target.value); setPage(1); }}><option value="">Any bedrooms</option><option value="2">2+ bedrooms</option><option value="3">3+ bedrooms</option><option value="4">4+ bedrooms</option></select></label><label className="filter-field"><span>Minimum baths</span><select aria-label="Minimum baths" className="live-input" value={minBaths} onChange={(event) => { setMinBaths(event.target.value); setPage(1); }}><option value="">Any bathrooms</option><option value="1">1+ bathroom</option><option value="2">2+ bathrooms</option><option value="3">3+ bathrooms</option></select></label></div><div className="filter-footer"><span><Filter size={14} /> RealtyAPI.io search route ready</span><button className="button button-primary" type="submit" disabled={loading}><Search size={16} /> {loading ? "Searching…" : "Search properties"}</button></div>{error && <div className="form-error" role="alert"><span>{error}</span>{accessIssue === "auth" ? <Link href={signInHref} className="button button-primary">Sign in to continue</Link> : accessIssue === "organization" ? <Link href="/settings" className="text-button">Review organization access</Link> : null}</div>}</form>
    <div className="split-layout search-split"><section className="panel"><header className="panel-heading"><div><h2>Search results</h2><p>{total ? `${total.toLocaleString()} source-backed listings` : "Paginated provider results with source-bound property handoff."}</p></div></header><div className="result-toolbar"><span>{results.length ? `Page ${page}` : "Awaiting search"}</span><div><button type="button" className="view-switch active">List</button><button type="button" className="view-switch" disabled>Map</button></div></div>{results.length ? <div className="live-results">{results.map((property) => <Link className="live-result" href={`/properties/${property.provider_property_id}?address=${encodeURIComponent(property.address)}`} key={property.provider_property_id}><div><strong>{property.address}</strong><span>{property.city}, {property.state} {property.zip_code} · {property.property_type}</span></div><div className="result-meta"><strong>{property.list_price ? `$${property.list_price.toLocaleString()}` : "Price unavailable"}</strong><span>{property.beds ?? "—"} bd · {property.baths ?? "—"} ba · {property.living_area ? `${property.living_area.toLocaleString()} sf` : "—"}</span><span className="result-provenance">Source: {property.source} · Updated {new Date(property.data_updated_at).toLocaleDateString()}</span></div><ArrowRight size={16} /></Link>)}</div> : <div className="empty-state"><span className="empty-icon"><Search size={22} /></span><h3>{error ? "Search could not be completed" : "No source records loaded"}</h3><p>{error || "Enter a location to retrieve live Realtor listings. No property record is inferred or seeded."}</p></div>}<div className="pagination"><button className="text-button" type="button" disabled={page <= 1 || loading} onClick={() => changePage(page - 1)}><ChevronLeft size={14} /> Previous</button><span>{results.length ? `Page ${page}` : "No page selected"}</span><button className="text-button" type="button" disabled={!hasNextPage || loading} onClick={() => changePage(page + 1)}>Next <ChevronRight size={14} /></button></div></section><section className="panel"><header className="panel-heading"><div><h2>Map exploration</h2><p>Only provider coordinates are placed on the map.</p></div></header><div className="map-placeholder"><MapPinned size={32} /><strong>{results.length ? "Map handoff available" : "Map awaits a search"}</strong><p>{results.length ? "Open a property to research its verified coordinates and history." : "Search with a city or ZIP to retrieve verified coordinates."}</p></div></section></div>
    <section className="panel"><header className="panel-heading"><div><h2>Saved-search entry points</h2><p>Saved criteria remain organization-scoped and require authenticated persistence.</p></div></header><div className="saved-search-grid"><div><strong>Investment criteria fit</strong><p>Property-fit scoring uses documented deterministic inputs, not an AI estimate.</p></div><div><strong>Freshness controls</strong><p>Every result includes RealtyAPI.io provenance and retrieval time.</p></div><div><strong>Research handoff</strong><p>Open a listing by provider property id to begin property intelligence review.</p></div></div></section>
  </>;
}
