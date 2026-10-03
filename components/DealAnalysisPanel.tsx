"use client";

import { FormEvent, useState } from "react";

type Metric = { state?: string; value?: number | null; classification?: string; formula?: string | null; reason?: string | null };
type AnalysisResult = Record<string, Metric>;

const fields = [
  ["arv", "ARV"], ["estimated_market_value", "Estimated market value"], ["outstanding_debt", "Outstanding debt"],
  ["repair_cost", "Repairs"], ["purchase_contract_price", "Purchase contract price"], ["expected_assignment_price", "Expected assignment price"],
  ["asking_price", "Asking price"], ["expected_sale_price", "Expected sale price"], ["mao_percentage", "MAO percentage"],
  ["desired_profit", "Desired profit"], ["transaction_costs", "Transaction costs"], ["holding_costs", "Holding costs"],
  ["financing_costs", "Financing costs"], ["other_costs", "Other costs"], ["total_invested_capital", "Total invested capital"], ["net_profit", "Net profit"],
] as const;

const resultLabels: Record<string, string> = { arv: "ARV", equity: "Equity", mao: "MAO", wholesale_spread: "Wholesale spread", wholesale_margin: "Wholesale margin", flip_profit: "Flip profit", roi: "ROI", price_vs_comps: "Price vs comps", price_vs_arv: "Price vs ARV", deal_score: "Deal score", risk_score: "Risk score", classification: "Classification" };

export function DealAnalysisPanel() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  function numberValue(key: string) { const raw = values[key]; return raw === undefined || raw === "" ? undefined : { classification: "USER_INPUT", value: Number(raw), source: "User-entered deal analysis input", confidence: "USER_PROVIDED" }; }
  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    const payload: Record<string, unknown> = { assumptions: {} };
    for (const [key] of fields) { const value = numberValue(key); if (!value) continue; if (["mao_percentage", "desired_profit", "transaction_costs", "holding_costs", "financing_costs", "other_costs", "total_invested_capital"].includes(key)) (payload.assumptions as Record<string, unknown>)[key] = value; else payload[key] = value; }
    try { const response = await fetch("/api/v1/deal-analysis", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body?.detail?.message ?? "Deterministic analysis is unavailable."); setResult(body); } catch (caught) { setResult(null); setError(caught instanceof Error ? caught.message : "Deterministic analysis is unavailable."); } finally { setLoading(false); }
  }
  return <div className="analysis-panel"><form onSubmit={submit}><div className="analysis-input-grid">{fields.map(([key, label]) => <label className="filter-field" key={key}><span>{label}<small>USER_INPUT</small></span><input className="live-input" inputMode="decimal" value={values[key] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.value }))} placeholder="UNKNOWN" /></label>)}</div><button className="button button-primary" type="submit" disabled={loading}>{loading ? "Calculating…" : "Run deterministic analysis"}</button></form>{error && <div className="form-error" role="alert">{error}</div>}{result && <div className="metric-grid analysis-results">{Object.entries(result).map(([key, metric]) => <div className="metric-card" key={key}><span>{resultLabels[key] ?? key}</span><strong>{metric.value === null || metric.value === undefined ? metric.state ?? "UNKNOWN" : `${metric.value}${key.includes("margin") || key === "roi" || key.includes("price_vs") ? "%" : ""}`}</strong><small>{metric.classification ?? "UNKNOWN"}{metric.formula ? ` · ${metric.formula}` : metric.reason ? ` · ${metric.reason}` : ""}</small></div>)}</div>}</div>;
}
