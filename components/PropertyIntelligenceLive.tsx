"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BadgeCheck, CircleAlert, FileLock2, Search, Target, UserRoundCheck } from "lucide-react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";

type ProviderProperty = {
  provider_property_id: string;
  provider_listing_id?: string | null;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: string;
  list_price?: number | null;
  beds?: number | null;
  baths?: number | null;
  living_area?: number | null;
  lot_size?: number | null;
  year_built?: number | null;
  listing_status?: string | null;
  days_on_market?: number | null;
  source: string;
  data_updated_at: string;
  photos?: string[];
};

function getOrganizationId(session: { user?: { app_metadata?: Record<string, unknown> } } | null) {
  const value = session?.user?.app_metadata?.organization_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

function Badge({ children = "UNKNOWN · No source record" }: { children?: React.ReactNode }) {
  return <span className="data-badge"><span />{children}</span>;
}

function valueOrUnknown(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "UNKNOWN" : String(value);
}

export function PropertyIntelligenceLive({ propertyId, address }: { propertyId: string; address?: string }) {
  const [property, setProperty] = useState<ProviderProperty | null>(null);
  const [loading, setLoading] = useState(Boolean(address));
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      if (!address) {
        setLoading(false);
        setError("This property link does not include its provider address. Return to live search and open the listing again.");
        return;
      }
      const persistedSession = getPersistedSupabaseSession();
      const client = getSupabaseBrowserClient();
      const session = client
        ? await Promise.race([client.auth.getSession().then(({ data }) => data.session).catch(() => null), new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500))])
        : null;
      const resolvedSession = session ?? persistedSession;
      const token = resolvedSession?.access_token;
      const organizationId = getOrganizationId(resolvedSession);
      if (!token || !organizationId) {
        if (active) {
          setLoading(false);
          setError(!token ? "Sign in to an approved workspace to retrieve this live property record." : "Your signed-in account is not assigned to an approved organization.");
        }
        return;
      }
      try {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), 25000);
        let response: Response;
        try {
          response = await fetch(`/api/v1/providers/property-detail?address=${encodeURIComponent(address)}`, { headers: { Authorization: `Bearer ${token}`, "X-Organization-Id": organizationId }, signal: controller.signal });
        } finally {
          window.clearTimeout(timeoutId);
        }
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body?.detail?.message ?? "The provider property detail could not be loaded.");
        if (active) setProperty(body as ProviderProperty);
      } catch (caught) {
        if (active) setError(caught instanceof Error ? caught.message : "The provider property detail could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [address]);

  const title = property?.address ?? (address || `Record ${propertyId}`);
  return <>
    <header className="screen-header"><div><p className="eyebrow">Research workspace</p><h1>Property intelligence</h1><p>{property ? "Verified provider record with source context intact." : error || `Resolving provider record ${propertyId}…`}</p></div><Link href="/properties" className="button button-secondary">Back to properties</Link></header>
    {loading ? <div className="status-banner"><Search size={18} /><p><strong>Retrieving verified property record.</strong> RealtyAPI.io detail data is loading for {title}.</p><span>LOADING</span></div> : error ? <div className="status-banner critical"><CircleAlert size={18}/><p><strong>Research unavailable.</strong> {error}</p><Badge /></div> : property ? <div className="status-banner"><BadgeCheck size={18}/><p><strong>Source-backed record loaded.</strong> {property.source} returned this property detail with provider freshness retained.</p><span>{new Date(property.data_updated_at).toLocaleDateString()}</span></div> : null}
    <div className="tab-strip"><button className="active">Details</button><button>Owner</button><button>Market</button><button>Comparable sales</button><button>Analysis</button><button>Motivation</button></div>
    <div className="research-grid"><section className="panel"><header className="panel-heading"><div><h2>Property facts</h2><p>Normalized from provider data; each field retains source and confidence.</p></div></header><dl className="fact-list"><div><dt>Address</dt><dd>{property ? property.address : "UNKNOWN"} {property && <Badge>realtyapi · VERIFIED</Badge>}</dd></div><div><dt>County</dt><dd>UNKNOWN · Provider detail does not return a county field</dd></div><div><dt>State / ZIP</dt><dd>{property ? `${valueOrUnknown(property.state)} · ${valueOrUnknown(property.zip_code)}` : "UNKNOWN"}</dd></div><div><dt>Property type</dt><dd>{valueOrUnknown(property?.property_type)}</dd></div><div><dt>Beds / baths / living area</dt><dd>{property ? `${valueOrUnknown(property.beds)} bd · ${valueOrUnknown(property.baths)} ba · ${property.living_area ? `${property.living_area.toLocaleString()} sf` : "UNKNOWN"}` : "UNKNOWN"}</dd></div><div><dt>Lot size / year built</dt><dd>{property ? `${property.lot_size ? `${property.lot_size.toLocaleString()} sf` : "UNKNOWN"} · ${valueOrUnknown(property.year_built)}` : "UNKNOWN"}</dd></div><div><dt>Listing status / days on market</dt><dd>{property ? `${valueOrUnknown(property.listing_status)} · ${property.days_on_market === null || property.days_on_market === undefined ? "UNKNOWN" : `${property.days_on_market} days`}` : "UNKNOWN"}</dd></div><div><dt>List price</dt><dd>{property?.list_price ? `$${property.list_price.toLocaleString()}` : "UNKNOWN"}</dd></div><div><dt>Last updated</dt><dd>{property ? `${property.source} · ${new Date(property.data_updated_at).toLocaleString()}` : "Not retrieved"}</dd></div></dl></section><section className="panel"><header className="panel-heading"><div><h2>Source photos</h2><p>Only photos returned by RealtyAPI are shown.</p></div></header>{property?.photos?.length ? <div className="photo-grid">{property.photos.map((photo) => <img key={photo} src={photo} alt="Provider-supplied property view" loading="lazy" />)}</div> : <div className="empty-state"><span className="empty-icon"><Search size={22} /></span><h3>Photos unavailable</h3><p>RealtyAPI did not supply photos for this record.</p></div>}</section><section className="panel"><header className="panel-heading"><div><h2>Research integrity</h2><p>Provider fields remain separate from calculated and unknown data.</p></div></header><div className="integrity-list"><div><BadgeCheck size={17}/><span><strong>Source-aware fields</strong><small>Provider, confidence, and verification time stay with every value.</small></span></div><div><UserRoundCheck size={17}/><span><strong>Owner information</strong><small>Only legally available contact details may be displayed.</small></span></div><div><FileLock2 size={17}/><span><strong>Correction trail</strong><small>User flags and overrides become auditable activity records.</small></span></div></div></section></div>
    <section className="panel"><header className="panel-heading"><div><h2>Comparable-sales review</h2><p>The deterministic comp engine records selection factors, outlier classification, scores, and exclusions.</p></div></header><div className="comp-controls"><span><label>Distance radius</label><strong>Requires configuration</strong></span><span><label>Recency window</label><strong>Requires configuration</strong></span><span><label>Size tolerance</label><strong>Requires configuration</strong></span><button className="button button-secondary" type="button" disabled>Recalculate ARV</button></div><div className="empty-state"><span className="empty-icon"><Target size={22} /></span><h3>Comparable provider unavailable</h3><p>No approved live comparable provider is configured. ARV remains INSUFFICIENT_DATA; no comparable records are fabricated.</p></div></section>
  </>;
}
