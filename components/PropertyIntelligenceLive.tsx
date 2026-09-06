"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowRight, BadgeCheck, CircleAlert, FileLock2, MapPinned, Search, ShieldCheck, Target, UserRoundCheck } from "lucide-react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";

type ProviderProperty = {
  provider_property_id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude?: number | null;
  longitude?: number | null;
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
  listing_url?: string | null;
};

type ViewKey = "details" | "owner" | "comps" | "map" | "underwriting" | "motivation";
type CompRow = { comparable_id: string; sale_price: string; distance_miles: string; sale_date: string; living_area_deviation: string; distance_score: string; recency_score: string; similarity_score: string; quality_score: string };
type CompAnalysis = { weighted_arv: number | null; arv_state: string; arv_reason?: string | null; included_comparable_count: number; median_sale_price?: number | null; median_absolute_deviation?: number | null; reviews: Array<{ comparable_id: string; eligible: boolean; outlier: boolean; excluded_reason?: string | null; comp_score?: number | null; effective_weight?: number | null }> };
type UnderwritingResponse = { arv: { state: string; value?: number | null; formula?: string | null; reason?: string | null }; equity: { state: string; value?: number | null; reason?: string | null }; mao: { state: string; value?: number | null; formula?: string | null; reason?: string | null }; wholesale_spread: { state: string; value?: number | null; reason?: string | null }; wholesale_margin: { state: string; value?: number | null; reason?: string | null }; flip_profit: { state: string; value?: number | null; reason?: string | null }; roi: { state: string; value?: number | null; reason?: string | null }; price_vs_arv: { state: string; value?: number | null; reason?: string | null }; explanation: string[] };
type HandoffResponse = { deal: { id: string; current_stage: string }; analysis: UnderwritingResponse; buyer_preview: Array<{ buyer: { id: string; name: string; company?: string | null; status?: string | null }; match: { match_score: number; confidence: string; match_reasons: string[]; failed_criteria: string[] } }>; matching_status: string };

function getOrganizationId(session: { user?: { app_metadata?: Record<string, unknown> } } | null) {
  const value = session?.user?.app_metadata?.organization_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

async function getAuthContext() {
  const persistedSession = getPersistedSupabaseSession();
  const client = getSupabaseBrowserClient();
  const session = client
    ? await Promise.race([
        client.auth.getSession().then(({ data }) => data.session).catch(() => null),
        new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500)),
      ])
    : null;
  const resolvedSession = session ?? persistedSession;
  return { token: resolvedSession?.access_token ?? null, organizationId: getOrganizationId(resolvedSession) };
}

function numberValue(value: string | number | null | undefined, classification: "USER_INPUT" | "CALCULATED_DATA" = "USER_INPUT") {
  if (value === "" || value === null || value === undefined || Number.isNaN(Number(value))) return { classification: "UNKNOWN" };
  return { value: Number(value), classification, source: classification === "CALCULATED_DATA" ? "deterministic comparable engine" : "workspace underwriting input", confidence: classification === "CALCULATED_DATA" ? "verified" : "user-approved" };
}

function Badge({ children = "UNKNOWN · No source record" }: { children?: React.ReactNode }) {
  return <span className="data-badge"><span />{children}</span>;
}

function valueOrUnknown(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "UNKNOWN" : String(value);
}

function money(value?: number | null) {
  return value === null || value === undefined ? "UNKNOWN" : `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function MetricCard({ label, metric }: { label: string; metric?: { state: string; value?: number | null; reason?: string | null } }) {
  const known = metric?.value !== null && metric?.value !== undefined;
  return <div className="metric-card"><span>{label}</span><strong>{known ? metric.value!.toLocaleString(undefined, { maximumFractionDigits: 2 }) : metric?.state ?? "UNKNOWN"}</strong><small>{known ? "CALCULATED_DATA" : metric?.reason ?? "Awaiting verified inputs"}</small></div>;
}

const emptyComp = (): CompRow => ({ comparable_id: "", sale_price: "", distance_miles: "", sale_date: "", living_area_deviation: "", distance_score: "", recency_score: "", similarity_score: "", quality_score: "" });

export function PropertyIntelligenceLive({ propertyId, address }: { propertyId: string; address?: string }) {
  const [property, setProperty] = useState<ProviderProperty | null>(null);
  const [loading, setLoading] = useState(Boolean(address));
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState<ViewKey>("details");
  const [compRows, setCompRows] = useState<CompRow[]>([emptyComp(), emptyComp(), emptyComp()]);
  const [compConfig, setCompConfig] = useState({ maxDistance: "1", maxAge: "180", maxDeviation: "20", outlierMad: "3" });
  const [compAnalysis, setCompAnalysis] = useState<CompAnalysis | null>(null);
  const [compError, setCompError] = useState("");
  const [underwriting, setUnderwriting] = useState({ purchase: "", repair: "", userArv: "", maoPercentage: "0.70", desiredProfit: "", assignment: "", sale: "", transaction: "", holding: "", financing: "", other: "", netProfit: "", invested: "", requiresFinancing: false });
  const [analysis, setAnalysis] = useState<UnderwritingResponse | null>(null);
  const [underwritingError, setUnderwritingError] = useState("");
  const [handoff, setHandoff] = useState<HandoffResponse | null>(null);
  const [handoffLoading, setHandoffLoading] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!address) {
        setLoading(false);
        setError("This property link does not include its provider address. Return to live search and open the listing again.");
        return;
      }
      const { token, organizationId } = await getAuthContext();
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
  const activeLabel = useMemo(() => ({ details: "Property facts", owner: "Owner details", comps: "Comparable sales", map: "Map", underwriting: "Deal underwriting", motivation: "Motivation signals" }[activeView]), [activeView]);

  async function analyzeComps(event: FormEvent) {
    event.preventDefault();
    setCompError("");
    const usable = compRows.filter((row) => row.comparable_id && row.sale_price && row.sale_date && row.distance_miles && row.living_area_deviation && row.distance_score && row.recency_score && row.similarity_score && row.quality_score);
    if (usable.length < 3) {
      setCompError("Enter at least three verified sold comparables. The authoritative engine will not return ARV with fewer qualified records.");
      return;
    }
    try {
      const response = await fetch("/api/v1/comparables/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ candidates: usable.map((row) => ({ comparable_id: row.comparable_id, sale_price: Number(row.sale_price), distance_miles: Number(row.distance_miles), sale_date: row.sale_date, living_area_deviation: Number(row.living_area_deviation), distance_score: Number(row.distance_score), recency_score: Number(row.recency_score), similarity_score: Number(row.similarity_score), quality_score: Number(row.quality_score) })), configuration: { search_date: new Date().toISOString().slice(0, 10), max_distance_miles: Number(compConfig.maxDistance), max_sale_age_days: Number(compConfig.maxAge), max_living_area_deviation: Number(compConfig.maxDeviation), minimum_comparable_count: 3, distance_weight: 0.35, recency_weight: 0.25, similarity_weight: 0.25, quality_weight: 0.15, outlier_mad_multiplier: Number(compConfig.outlierMad) } }) });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body?.detail?.message ?? "Comparable analysis could not be completed.");
      setCompAnalysis(body as CompAnalysis);
      if (body?.weighted_arv) setUnderwriting((current) => ({ ...current, userArv: String(body.weighted_arv) }));
    } catch (caught) {
      setCompError(caught instanceof Error ? caught.message : "Comparable analysis could not be completed.");
    }
  }

  function analysisPayload() {
    const arv = compAnalysis?.weighted_arv ?? (underwriting.userArv ? Number(underwriting.userArv) : null);
    return {
      arv: numberValue(arv, compAnalysis?.weighted_arv ? "CALCULATED_DATA" : "USER_INPUT"),
      estimated_market_value: numberValue(property?.list_price ?? null, "CALCULATED_DATA"),
      outstanding_debt: { classification: "UNKNOWN" },
      repair_cost: numberValue(underwriting.repair),
      purchase_contract_price: numberValue(underwriting.purchase),
      expected_assignment_price: numberValue(underwriting.assignment),
      asking_price: numberValue(property?.list_price ?? null, "USER_INPUT"),
      expected_sale_price: numberValue(underwriting.sale),
      net_profit: numberValue(underwriting.netProfit),
      assumptions: { mao_percentage: numberValue(underwriting.maoPercentage), desired_profit: numberValue(underwriting.desiredProfit), transaction_costs: numberValue(underwriting.transaction), holding_costs: numberValue(underwriting.holding), financing_costs: numberValue(underwriting.financing), other_costs: numberValue(underwriting.other), total_invested_capital: numberValue(underwriting.invested) },
    };
  }

  async function calculateUnderwriting(event: FormEvent) {
    event.preventDefault();
    setUnderwritingError("");
    try {
      const { token } = await getAuthContext();
      if (!token) throw new Error("Sign in to calculate a protected underwriting result.");
      const response = await fetch("/api/v1/deal-analysis", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(analysisPayload()) });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body?.detail?.message ?? "Underwriting could not be calculated.");
      setAnalysis(body as UnderwritingResponse);
    } catch (caught) {
      setUnderwritingError(caught instanceof Error ? caught.message : "Underwriting could not be calculated.");
    }
  }

  async function handoffToCrm() {
    setHandoffLoading(true);
    setUnderwritingError("");
    try {
      const { token, organizationId } = await getAuthContext();
      if (!token || !organizationId) throw new Error("Sign in to an approved organization before creating a CRM deal.");
      const response = await fetch("/api/v1/underwriting/handoff", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, "X-Organization-Id": organizationId }, body: JSON.stringify({ address: title, property_id: propertyId, purchase_contract_price: Number(underwriting.purchase), repair_cost: underwriting.repair ? Number(underwriting.repair) : null, arv: compAnalysis?.weighted_arv ?? (underwriting.userArv ? Number(underwriting.userArv) : null), arv_classification: compAnalysis?.weighted_arv ? "CALCULATED_DATA" : "USER_INPUT", mao_percentage: underwriting.maoPercentage ? Number(underwriting.maoPercentage) : null, desired_profit: underwriting.desiredProfit ? Number(underwriting.desiredProfit) : null, expected_assignment_price: underwriting.assignment ? Number(underwriting.assignment) : null, expected_sale_price: underwriting.sale ? Number(underwriting.sale) : null, transaction_costs: underwriting.transaction ? Number(underwriting.transaction) : null, holding_costs: underwriting.holding ? Number(underwriting.holding) : null, financing_costs: underwriting.financing ? Number(underwriting.financing) : null, other_costs: underwriting.other ? Number(underwriting.other) : null, net_profit: underwriting.netProfit ? Number(underwriting.netProfit) : null, total_invested_capital: underwriting.invested ? Number(underwriting.invested) : null, requires_financing: underwriting.requiresFinancing, buyer_match_market: property?.city ?? null }) });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body?.detail?.message ?? "CRM handoff could not be completed.");
      setHandoff(body as HandoffResponse);
    } catch (caught) {
      setUnderwritingError(caught instanceof Error ? caught.message : "CRM handoff could not be completed.");
    } finally {
      setHandoffLoading(false);
    }
  }

  const updateComp = (index: number, field: keyof CompRow, value: string) => setCompRows((rows) => rows.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: value } : row));
  const updateUnderwriting = (field: keyof typeof underwriting, value: string | boolean) => setUnderwriting((current) => ({ ...current, [field]: value }));

  return <>
    <header className="screen-header"><div><p className="eyebrow">Research workspace</p><h1>Property intelligence</h1><p>{property ? "Verified provider record with source context intact." : error || `Resolving provider record ${propertyId}…`}</p></div><Link href="/properties" className="button button-secondary">Back to properties</Link></header>
    {loading ? <div className="status-banner"><Search size={18} /><p><strong>Retrieving verified property record.</strong> RealtyAPI.io detail data is loading for {title}.</p><span>LOADING</span></div> : error ? <div className="status-banner critical"><CircleAlert size={18}/><p><strong>Research unavailable.</strong> {error}</p><Badge /></div> : property ? <div className="status-banner"><BadgeCheck size={18}/><p><strong>Source-backed record loaded.</strong> {property.source} returned this property detail with provider freshness retained.</p><span>{new Date(property.data_updated_at).toLocaleDateString()}</span></div> : null}
    <div className="property-action-bar"><div><span className="eyebrow">Verified property</span><strong>{title}</strong><small>{property?.city}, {property?.state} {property?.zip_code} · {activeLabel}</small></div><div className="property-action-buttons">{([ ["details", "Details"], ["owner", "Owner details"], ["comps", "Comparable sales"], ["map", "Map"], ["underwriting", "Deal underwriting"], ["motivation", "Motivation"] ] as Array<[ViewKey, string]>).map(([key, label]) => <button key={key} type="button" className={`button ${activeView === key ? "button-primary" : "button-secondary"}`} onClick={() => setActiveView(key)}>{label}</button>)}</div></div>
    {activeView === "details" && <div className="research-grid"><section className="panel"><header className="panel-heading"><div><h2>Property facts</h2><p>Normalized from provider data; each field retains source and confidence.</p></div></header><dl className="fact-list"><div><dt>Address</dt><dd>{property ? property.address : "UNKNOWN"} {property && <Badge>realtyapi · VERIFIED</Badge>}</dd></div><div><dt>Property type</dt><dd>{valueOrUnknown(property?.property_type)}</dd></div><div><dt>Beds / baths / living area</dt><dd>{property ? `${valueOrUnknown(property.beds)} bd · ${valueOrUnknown(property.baths)} ba · ${property.living_area ? `${property.living_area.toLocaleString()} sf` : "UNKNOWN"}` : "UNKNOWN"}</dd></div><div><dt>Listing status / days on market</dt><dd>{property ? `${valueOrUnknown(property.listing_status)} · ${property.days_on_market === null || property.days_on_market === undefined ? "UNKNOWN" : `${property.days_on_market} days`}` : "UNKNOWN"}</dd></div><div><dt>List price</dt><dd>{money(property?.list_price)}</dd></div><div><dt>Last updated</dt><dd>{property ? `${property.source} · ${new Date(property.data_updated_at).toLocaleString()}` : "Not retrieved"}</dd></div></dl></section><section className="panel"><header className="panel-heading"><div><h2>Research integrity</h2><p>Provider fields remain separate from calculated and unknown data.</p></div></header><div className="integrity-list"><div><BadgeCheck size={17}/><span><strong>Source-aware fields</strong><small>Provider, confidence, and verification time stay with every value.</small></span></div><div><UserRoundCheck size={17}/><span><strong>Owner information</strong><small>Only legally available contact details may be displayed.</small></span></div><div><FileLock2 size={17}/><span><strong>Correction trail</strong><small>User flags and overrides become auditable activity records.</small></span></div></div></section></div>}
    {activeView === "owner" && <section className="panel workflow-panel"><header className="panel-heading"><div><h2>Owner details</h2><p>Owner data is a separate provider capability and must retain field-level provenance.</p></div><Badge>OWNER DATA · UNKNOWN</Badge></header><div className="empty-state"><span className="empty-icon"><UserRoundCheck size={22} /></span><h3>No verified owner record returned</h3><p>The connected RealtyAPI detail contract currently returns property facts only. No owner name, mailing address, mortgage, phone, or email is inferred. Connect an approved owner-data provider to populate this panel.</p></div></section>}
    {activeView === "map" && <section className="panel workflow-panel"><header className="panel-heading"><div><h2>Verified map location</h2><p>Only provider coordinates are rendered; no address geocoding is inferred.</p></div><Badge>{property?.latitude !== null && property?.latitude !== undefined && property?.longitude !== null && property?.longitude !== undefined ? "COORDINATES · VERIFIED" : "COORDINATES · UNKNOWN"}</Badge></header>{property?.latitude !== null && property?.latitude !== undefined && property?.longitude !== null && property?.longitude !== undefined ? <div className="map-detail-card"><div className="map-grid"><MapPinned size={34}/><div><strong>{property.address}</strong><span>{property.latitude.toFixed(6)}, {property.longitude.toFixed(6)}</span><small>Source: {property.source} · Updated {new Date(property.data_updated_at).toLocaleString()}</small></div></div><a className="button button-primary" href={`https://www.openstreetmap.org/?mlat=${property.latitude}&mlon=${property.longitude}#map=17/${property.latitude}/${property.longitude}`} target="_blank" rel="noreferrer">Open verified map <ArrowRight size={15}/></a></div> : <div className="empty-state"><span className="empty-icon"><MapPinned size={22}/></span><h3>Coordinates unavailable</h3><p>The provider did not return latitude and longitude for this record. SCALEESTATE does not geocode or approximate a location.</p></div>}</section>}
    {activeView === "comps" && <section className="panel workflow-panel"><header className="panel-heading"><div><h2>Comparable-sales review</h2><p>Enter verified sold records to run the deterministic selection, outlier, weighting, and ARV engine.</p></div><Badge>{compAnalysis ? `${compAnalysis.arv_state} · ${compAnalysis.included_comparable_count} INCLUDED` : "NO COMPS ANALYZED"}</Badge></header><form onSubmit={analyzeComps}><div className="comp-controls"><label>Max distance (mi)<input className="live-input" type="number" min="0.1" step="0.1" value={compConfig.maxDistance} onChange={(event) => setCompConfig({ ...compConfig, maxDistance: event.target.value })}/></label><label>Max age (days)<input className="live-input" type="number" min="1" value={compConfig.maxAge} onChange={(event) => setCompConfig({ ...compConfig, maxAge: event.target.value })}/></label><label>Size deviation (%)<input className="live-input" type="number" min="0" value={compConfig.maxDeviation} onChange={(event) => setCompConfig({ ...compConfig, maxDeviation: event.target.value })}/></label><label>Outlier MAD ×<input className="live-input" type="number" min="0.1" step="0.1" value={compConfig.outlierMad} onChange={(event) => setCompConfig({ ...compConfig, outlierMad: event.target.value })}/></label></div><div className="comp-entry-grid">{compRows.map((row, index) => <div className="comp-entry" key={index}><strong>Verified comp {index + 1}</strong>{([ ["comparable_id", "Comp id"], ["sale_price", "Sale price"], ["distance_miles", "Distance (mi)"], ["sale_date", "Sale date"], ["living_area_deviation", "Size deviation"], ["distance_score", "Distance score"], ["recency_score", "Recency score"], ["similarity_score", "Similarity score"], ["quality_score", "Quality score"] ] as Array<[keyof CompRow, string]>).map(([field, label]) => <label key={field}>{label}<input className="live-input" type={field === "sale_date" ? "date" : field === "comparable_id" ? "text" : "number"} min={field.includes("score") ? "0" : field === "living_area_deviation" ? "0" : undefined} max={field.includes("score") ? "1" : undefined} step={field.includes("score") || field.includes("distance") || field.includes("deviation") ? "0.01" : undefined} value={row[field]} onChange={(event) => updateComp(index, field, event.target.value)} /></label>)}</div>)}</div>{compError && <div className="form-error" role="alert">{compError}</div>}<button className="button button-primary" type="submit"><Target size={16}/> Calculate deterministic ARV</button></form>{compAnalysis && <div className="analysis-result"><div className="metric-grid"><MetricCard label="Weighted ARV" metric={{ state: compAnalysis.arv_state, value: compAnalysis.weighted_arv, reason: compAnalysis.arv_reason }}/><MetricCard label="Included comps" metric={{ state: compAnalysis.arv_state, value: compAnalysis.included_comparable_count }}/><MetricCard label="Median sale" metric={{ state: compAnalysis.arv_state, value: compAnalysis.median_sale_price }}/><MetricCard label="MAD" metric={{ state: compAnalysis.arv_state, value: compAnalysis.median_absolute_deviation }}/></div><p className="configuration-note">{compAnalysis.arv_reason ?? "ARV is calculated from the normalized weighted comparable contributions returned by the backend."}</p><button className="button button-secondary" type="button" onClick={() => setActiveView("underwriting")}>Continue to deal underwriting <ArrowRight size={15}/></button></div>}</section>}
    {activeView === "motivation" && <section className="panel workflow-panel"><header className="panel-heading"><div><h2>Motivation signals</h2><p>Signals are evidence, not proof of seller motivation.</p></div><Badge>MOTIVATION · UNKNOWN</Badge></header><div className="empty-state"><span className="empty-icon"><ShieldCheck size={22}/></span><h3>Awaiting verified owner and market evidence</h3><p>Motivation scoring remains unavailable until the approved owner, tax, foreclosure, vacancy, and listing-history sources are connected.</p></div></section>}
    {activeView === "underwriting" && <section className="panel workflow-panel"><header className="panel-heading"><div><h2>Deal underwriting</h2><p>Backend-only calculations. Every missing input stays UNKNOWN; AI cannot calculate or overwrite metrics.</p></div><Badge>{analysis ? "CALCULATION READY" : "INPUT REQUIRED"}</Badge></header><form className="underwriting-form" onSubmit={calculateUnderwriting}><div className="underwriting-fields">{([ ["purchase", "Purchase / contract price", true], ["repair", "Repair cost", false], ["userArv", "ARV override if no comps", false], ["maoPercentage", "MAO percentage", false], ["desiredProfit", "Desired profit", false], ["assignment", "Expected assignment price", false], ["sale", "Expected sale price", false], ["transaction", "Transaction costs", false], ["holding", "Holding costs", false], ["financing", "Financing costs", false], ["other", "Other costs", false], ["netProfit", "Net profit for ROI", false], ["invested", "Total invested capital", false] ] as Array<[keyof typeof underwriting, string, boolean]>).map(([field, label, required]) => <label key={field}>{label}{field === "userArv" && compAnalysis?.weighted_arv ? <small>Weighted ARV from comps: {money(compAnalysis.weighted_arv)}</small> : null}<input className="live-input" required={required} type="number" min="0" step="0.01" value={underwriting[field] as string} onChange={(event) => updateUnderwriting(field, event.target.value)} /></label>)}<label className="check-field"><input type="checkbox" checked={underwriting.requiresFinancing} onChange={(event) => updateUnderwriting("requiresFinancing", event.target.checked)}/> Requires financing</label></div><p className="configuration-note">MAO follows the authoritative formula: ARV × configured MAO percentage − repair cost − desired profit. Transaction, holding, financing, and other costs are never assumed to be zero.</p>{underwritingError && <div className="form-error" role="alert">{underwritingError}</div>}<div className="underwriting-actions"><button className="button button-primary" type="submit"><Target size={16}/> Calculate underwriting</button><button className="button button-secondary" type="button" disabled={!analysis || handoffLoading || !underwriting.purchase} onClick={() => void handoffToCrm()}>{handoffLoading ? "Creating CRM handoff…" : "Send to CRM + buyer preview"}</button></div></form>{analysis && <div className="analysis-result"><div className="metric-grid"><MetricCard label="ARV" metric={analysis.arv}/><MetricCard label="MAO" metric={analysis.mao}/><MetricCard label="Wholesale spread" metric={analysis.wholesale_spread}/><MetricCard label="Wholesale margin" metric={analysis.wholesale_margin}/><MetricCard label="Flip profit" metric={analysis.flip_profit}/><MetricCard label="ROI" metric={analysis.roi}/><MetricCard label="Price vs ARV" metric={analysis.price_vs_arv}/><MetricCard label="Equity" metric={analysis.equity}/></div><div className="explanation-list">{analysis.explanation.map((line) => <span key={line}><ShieldCheck size={14}/>{line}</span>)}</div></div>}{handoff && <div className="handoff-result"><div className="status-banner"><BadgeCheck size={18}/><p><strong>CRM handoff complete.</strong> Deal {handoff.deal.id} was created at {handoff.deal.current_stage}; immutable analysis snapshot and audit/activity records were written.</p><span>{handoff.matching_status}</span></div><h3>Buyer-fit preview</h3>{handoff.buyer_preview.length ? <div className="buyer-preview-list">{handoff.buyer_preview.map((item) => <div className="buyer-preview" key={item.buyer.id}><div><strong>{item.buyer.name}</strong><span>{item.buyer.company ?? "Organization buyer"} · {item.match.confidence} confidence</span></div><b>{Math.round(item.match.match_score * 100)}%</b><small>{item.match.match_reasons.join(" · ") || "No matched criteria recorded"}{item.match.failed_criteria.length ? ` | Failed: ${item.match.failed_criteria.join(" · ")}` : ""}</small></div>)}</div> : <div className="empty-state"><span className="empty-icon"><UserRoundCheck size={22}/></span><h3>No active buyers with criteria</h3><p>The deal is in CRM, but buyer-fit preview is empty until organization buyers and structured criteria are available.</p></div>}<Link href={`/deals/${handoff.deal.id}`} className="button button-secondary">Open CRM deal workspace <ArrowRight size={15}/></Link></div>}</section>}
  </>;
}
