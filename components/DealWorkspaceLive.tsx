"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, BadgeCheck, CircleAlert, Clock3, FileLock2, ShieldCheck, UserRoundCheck } from "lucide-react";
import { getPersistedSupabaseSession, getSupabaseBrowserClient } from "@/lib/supabase-browser";

type DealPayload = { deal: { id: string; current_stage: string; purchase_price?: number | null; contract_price?: number | null; property_id?: string | null; created_at?: string }; analysis?: { result?: Record<string, { state?: string; value?: number | null; reason?: string | null }> } | null; snapshot?: { snapshot_type?: string; created_at?: string } | null; buyer_matches: Array<{ buyer_id: string; match_score: number; confidence: string; match_reasons: string[]; failed_criteria: string[] }>; activities: Array<{ activity_type: string; description: string; created_at: string }> };

function metric(result: DealPayload["analysis"], key: string) {
  const value = result?.result?.[key];
  return value?.value === null || value?.value === undefined ? value?.state ?? "UNKNOWN" : value.value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function DealWorkspaceLive({ dealId }: { dealId: string }) {
  const [payload, setPayload] = useState<DealPayload | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [matchingMessage, setMatchingMessage] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      const persisted = getPersistedSupabaseSession();
      const client = getSupabaseBrowserClient();
      const session = client ? await Promise.race([client.auth.getSession().then(({ data }) => data.session).catch(() => null), new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500))]) : null;
      const resolved = session ?? persisted;
      const organizationId = resolved?.user?.app_metadata?.organization_id;
      if (!resolved?.access_token || typeof organizationId !== "string") {
        if (active) { setError("Sign in to an approved organization to load this CRM deal workspace."); setLoading(false); }
        return;
      }
      try {
        const response = await fetch(`/api/v1/deals/${encodeURIComponent(dealId)}`, { headers: { Authorization: `Bearer ${resolved.access_token}`, "X-Organization-Id": organizationId } });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body?.detail?.message ?? "The CRM deal could not be loaded.");
        if (active) setPayload(body as DealPayload);
      } catch (caught) { if (active) setError(caught instanceof Error ? caught.message : "The CRM deal could not be loaded."); }
      finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; };
  }, [dealId]);

  async function runOfficialMatching() {
    if (!payload) return;
    setMatching(true); setMatchingMessage("");
    const persisted = getPersistedSupabaseSession();
    const client = getSupabaseBrowserClient();
    const session = client ? await Promise.race([client.auth.getSession().then(({ data }) => data.session).catch(() => null), new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 1500))]) : null;
    const resolved = session ?? persisted;
    const organizationId = resolved?.user?.app_metadata?.organization_id;
    if (!resolved?.access_token || typeof organizationId !== "string") { setMatching(false); setMatchingMessage("Sign in to run official matching."); return; }
    const response = await fetch(`/api/v1/deals/${encodeURIComponent(dealId)}/match-buyers`, { method: "POST", headers: { Authorization: `Bearer ${resolved.access_token}`, "X-Organization-Id": organizationId } });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) setMatchingMessage(body?.detail?.message ?? "Official matching is unavailable until the deal reaches Under Contract.");
    else setMatchingMessage(`Official matching completed for ${body.matches?.length ?? 0} organization buyers.`);
    setMatching(false);
  }

  return <><header className="screen-header"><div><p className="eyebrow">CRM deal workspace</p><h1>Underwriting handoff</h1><p>{payload ? `Deal ${dealId} · ${payload.deal.current_stage}` : error || "Loading persisted CRM evidence…"}</p></div><Link href="/deals" className="button button-secondary"><ArrowLeft size={15}/> Back to deals</Link></header>{loading && <div className="status-banner"><Clock3 size={18}/><p><strong>Loading CRM evidence.</strong> Organization-scoped deal, snapshot, buyer-match, and activity records are being retrieved.</p><span>LOADING</span></div>}{error && <div className="status-banner critical"><CircleAlert size={18}/><p><strong>CRM unavailable.</strong> {error}</p><span>ACCESS REQUIRED</span></div>}{payload && <><div className="status-banner"><BadgeCheck size={18}/><p><strong>CRM record loaded.</strong> The deal has a persisted underwriting handoff and can progress through documented stage transitions.</p><span>{payload.deal.current_stage}</span></div><div className="pipeline-summary"><span><strong>{payload.deal.current_stage}</strong> Stage</span><span><strong>{payload.buyer_matches.length}</strong> Official matches</span><span><strong>{payload.snapshot ? "YES" : "NO"}</strong> Snapshot</span><span><strong>{payload.activities.length}</strong> Activities</span></div><div className="deal-columns"><div><section className="panel"><header className="panel-heading"><div><h2>Deterministic analysis snapshot</h2><p>Values are backend outputs with explicit UNKNOWN states preserved.</p></div><ShieldCheck size={18}/></header><div className="metric-grid"><div className="metric-card"><span>ARV</span><strong>{metric(payload.analysis, "arv")}</strong><small>CALCULATED_DATA</small></div><div className="metric-card"><span>MAO</span><strong>{metric(payload.analysis, "mao")}</strong><small>CALCULATED_DATA</small></div><div className="metric-card"><span>Wholesale spread</span><strong>{metric(payload.analysis, "wholesale_spread")}</strong><small>CALCULATED_DATA</small></div><div className="metric-card"><span>ROI</span><strong>{metric(payload.analysis, "roi")}</strong><small>CALCULATED_DATA</small></div><div className="metric-card"><span>Flip profit</span><strong>{metric(payload.analysis, "flip_profit")}</strong><small>CALCULATED_DATA</small></div><div className="metric-card"><span>Risk</span><strong>{metric(payload.analysis, "risk_score")}</strong><small>CONFIGURATION_REQUIRED may be valid</small></div></div></section><section className="panel"><header className="panel-heading"><div><h2>Activity timeline</h2><p>Append-only workflow events.</p></div><Clock3 size={18}/></header><div className="activity-list">{payload.activities.length ? payload.activities.map((activity) => <div className="evidence-row" key={`${activity.activity_type}-${activity.created_at}`}><span className="evidence-label"><BadgeCheck size={14}/>{activity.description}</span><span className="evidence-value">{new Date(activity.created_at).toLocaleString()}</span></div>) : <div className="empty-state"><Clock3 size={21}/><h3>No activity records</h3><p>The handoff activity record was not returned by the organization data store.</p></div>}</div></section></div><aside className="deal-side"><section className="panel"><header className="panel-heading"><div><h2>Buyer matching</h2><p>Official matching is gated by Under Contract.</p></div><UserRoundCheck size={18}/></header>{payload.deal.current_stage === "UNDER_CONTRACT" || payload.deal.current_stage === "BUYER_SEARCH" ? <button className="button button-primary full" type="button" disabled={matching} onClick={() => void runOfficialMatching()}>{matching ? "Matching buyers…" : "Run official buyer matching"}</button> : <div className="locked-block"><FileLock2 size={22}/><strong>Preview available; official matching locked</strong><p>The underwriting handoff creates the CRM record and buyer-fit preview. Transition the deal through Under Contract to persist official buyer matches.</p></div>}{matchingMessage && <p className="configuration-note">{matchingMessage}</p>}{payload.buyer_matches.length ? <div className="buyer-preview-list">{payload.buyer_matches.map((match) => <div className="buyer-preview" key={match.buyer_id}><div><strong>Buyer {match.buyer_id.slice(0, 8)}</strong><span>{match.confidence} confidence</span></div><b>{Math.round(match.match_score * 100)}%</b><small>{match.match_reasons.join(" · ") || "No matched criteria"}</small></div>)}</div> : null}</section><section className="panel"><header className="panel-heading"><div><h2>Snapshot integrity</h2><p>{payload.snapshot ? `${payload.snapshot.snapshot_type} · ${new Date(payload.snapshot.created_at ?? Date.now()).toLocaleString()}` : "No snapshot returned"}</p></div><FileLock2 size={18}/></header><p className="configuration-note">The analysis inputs, provider facts, formula outputs, and active handoff configuration are retained for audit review.</p></section></aside></div></>}</>;
}
