"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ArrowRight, ChevronLeft, ChevronRight, Filter, MapPinned, Search, ShieldCheck } from "lucide-react";

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
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<PropertyResult[]>([]);
  const [total, setTotal] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event?: FormEvent, requestedPage = 1) {
    event?.preventDefault();
    setPage(requestedPage);
    if (!location.trim()) {
      setError("Enter a city, ZIP code, neighborhood, or county to search.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/v1/providers/property-search?location=${encodeURIComponent(location.trim())}&page=${requestedPage}&limit=50`);
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail?.message ?? "Property search is unavailable.");
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
    <div className="status-banner"><ShieldCheck size={18} /><p><strong>Live provider connected.</strong> RealtyAPI.io is configured server-side. Search requests still require an authenticated workspace and organization scope before results are returned.</p><span>REALTYAPI.IO</span></div>
    <form className="panel filter-panel" onSubmit={submit}><div className="filter-topline"><div><span className="eyebrow">Search criteria</span><p>Search by city, ZIP, neighborhood, or county. Every result retains provider freshness.</p></div><Link href="/search" className="text-button"><Filter size={15} /> Saved criteria</Link></div><div className="filters"><label className="filter-field wide"><span>Location</span><input className="live-input" value={location} onChange={(event) => { setLocation(event.target.value); setPage(1); }} placeholder="Austin, TX or 78744" /></label><div className="filter-field"><span>Property type</span><button type="button">All property types <ChevronRight size={14} /></button></div><div className="filter-field"><span>Listing status</span><button type="button">Active & pending <ChevronRight size={14} /></button></div><div className="filter-field"><span>Purchase price</span><button type="button">Any price <ChevronRight size={14} /></button></div><div className="filter-field"><span>Beds / baths</span><button type="button">Any configuration <ChevronRight size={14} /></button></div></div><div className="filter-footer"><span><Filter size={14} /> RealtyAPI.io search route ready</span><button className="button button-primary" type="submit" disabled={loading}><Search size={16} /> {loading ? "Searching…" : "Search properties"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}</form>
    <div className="split-layout search-split"><section className="panel"><header className="panel-heading"><div><h2>Search results</h2><p>{total ? `${total.toLocaleString()} source-backed listings` : "Paginated provider results with source-bound property handoff."}</p></div></header><div className="result-toolbar"><span>{results.length ? `Page ${page}` : "Awaiting search"}</span><div><button type="button" className="view-switch active">List</button><button type="button" className="view-switch" disabled>Map</button></div></div>{results.length ? <div className="live-results">{results.map((property) => <Link className="live-result" href={`/properties/${property.provider_property_id}`} key={property.provider_property_id}><div><strong>{property.address}</strong><span>{property.city}, {property.state} {property.zip_code} · {property.property_type}</span></div><div className="result-meta"><strong>{property.list_price ? `$${property.list_price.toLocaleString()}` : "Price unavailable"}</strong><span>{property.beds ?? "—"} bd · {property.baths ?? "—"} ba · {property.living_area ? `${property.living_area.toLocaleString()} sf` : "—"}</span><span className="result-provenance">Source: {property.source} · Updated {new Date(property.data_updated_at).toLocaleDateString()}</span></div><ArrowRight size={16} /></Link>)}</div> : <div className="empty-state"><span className="empty-icon"><Search size={22} /></span><h3>{error ? "Search could not be completed" : "No source records loaded"}</h3><p>{error || "Enter a location to retrieve live Realtor listings. No property record is inferred or seeded."}</p></div>}<div className="pagination"><button className="text-button" type="button" disabled={page <= 1 || loading} onClick={() => changePage(page - 1)}><ChevronLeft size={14} /> Previous</button><span>{results.length ? `Page ${page}` : "No page selected"}</span><button className="text-button" type="button" disabled={!hasNextPage || loading} onClick={() => changePage(page + 1)}>Next <ChevronRight size={14} /></button></div></section><section className="panel"><header className="panel-heading"><div><h2>Map exploration</h2><p>Only provider coordinates are placed on the map.</p></div></header><div className="map-placeholder"><MapPinned size={32} /><strong>{results.length ? "Map handoff available" : "Map awaits a search"}</strong><p>{results.length ? "Open a property to research its verified coordinates and history." : "Search with a city or ZIP to retrieve verified coordinates."}</p></div></section></div>
    <section className="panel"><header className="panel-heading"><div><h2>Saved-search entry points</h2><p>Saved criteria remain organization-scoped and require authenticated persistence.</p></div></header><div className="saved-search-grid"><div><strong>Investment criteria fit</strong><p>Property-fit scoring uses documented deterministic inputs, not an AI estimate.</p></div><div><strong>Freshness controls</strong><p>Every result includes RealtyAPI.io provenance and retrieval time.</p></div><div><strong>Research handoff</strong><p>Open a listing by provider property id to begin property intelligence review.</p></div></div></section>
  </>;
}
