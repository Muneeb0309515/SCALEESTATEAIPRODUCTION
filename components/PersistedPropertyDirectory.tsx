"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CircleAlert, Filter, MapPinned, Search } from "lucide-react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";

type PersistedProperty = {
  organization_property_id?: string | null;
  provider_property_id?: string | null;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: string;
  list_price?: number | null;
  listing_status?: string | null;
  source?: string | null;
  data_updated_at?: string | null;
  source_retrieved_at?: string | null;
  provenance?: Record<string, unknown>;
};

function getOrganizationId(session: { user?: { app_metadata?: Record<string, unknown> } } | null) {
  const value = session?.user?.app_metadata?.organization_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

export function PersistedPropertyDirectory() {
  const [properties, setProperties] = useState<PersistedProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const client = getSupabaseBrowserClient();
        const persistedSession = getPersistedSupabaseSession();
        const session = client
          ? await Promise.race([
              client.auth.getSession().then(({ data }) => data.session).catch(() => null),
              new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500)),
            ])
          : null;
        const resolvedSession = session ?? persistedSession;
        const token = resolvedSession?.access_token;
        const organizationId = getOrganizationId(resolvedSession);
        if (!token) throw new Error("Sign in to an approved workspace to load persisted properties.");
        if (!organizationId) throw new Error("Your signed-in account is not assigned to an approved organization.");
        const response = await fetch("/api/v1/properties", {
          headers: { Authorization: `Bearer ${token}`, "X-Organization-Id": organizationId },
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body?.detail?.message ?? "Persisted properties could not be loaded.");
        if (active) setProperties(Array.isArray(body) ? body : []);
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught.message : "Persisted properties could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, []);

  return <>
    <header className="screen-header"><div><p className="eyebrow">Property intelligence</p><h1>Property records with provenance intact.</h1><p>Review research-ready properties retrieved for your organization.</p></div><Link href="/search" className="button button-primary"><Search size={16} /> Search properties</Link></header>
    {error && <div className="status-banner critical"><CircleAlert size={18} /><p><strong>Properties unavailable.</strong> {error}</p><span>ERROR</span></div>}
    <section className="panel"><header className="panel-heading"><div><h2>Property directory</h2><p>Only persisted organization-scoped records are shown.</p></div></header>
      <div className="table-toolbar"><span>{loading ? "Loading properties…" : `${properties.length} properties`}</span><button type="button" className="text-button" disabled><Filter size={15} /> Filter</button></div>
      {loading ? <div className="empty-state"><span className="empty-icon"><Search size={22} /></span><h3>Loading persisted records</h3><p>Checking authenticated organization access.</p></div> : properties.length === 0 && !error ? <div className="empty-state"><span className="empty-icon"><MapPinned size={22} /></span><h3>No property records</h3><p>Run a verified RealtyAPI search to create the first persisted property record.</p><Link href="/search" className="button button-secondary">Start a search</Link></div> : <div className="data-table">{properties.map((property) => <Link key={property.organization_property_id ?? property.provider_property_id} href={`/properties/${property.organization_property_id}`} className="table-row"><span><strong>{property.address}</strong><small>{property.city}, {property.state} {property.zip_code}</small></span><span>{property.property_type}<small>{property.listing_status ?? "UNKNOWN"}</small></span><span>{property.list_price ? `$${property.list_price.toLocaleString()}` : "UNKNOWN"}<small>{property.source ?? "UNKNOWN"} · provenance retained</small></span><span>{property.organization_property_id ? "Persisted" : "UNKNOWN"}<small>{property.source_retrieved_at ? new Date(property.source_retrieved_at).toLocaleDateString() : "Retrieval time UNKNOWN"}</small></span></Link>)}</div>}
    </section>
  </>;
}
