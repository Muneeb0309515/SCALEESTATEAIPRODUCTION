"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { CircleAlert, LoaderCircle } from "lucide-react";
import {
  getSupabaseBrowserClient,
  getSupabaseSessionScopeKey,
  observeSupabaseSession,
} from "@/lib/supabase-browser";

type Metric = {
  state?: string;
  value?: number | null;
  classification?: string;
  formula?: string | null;
  reason?: string | null;
};
type AnalysisResult = Record<string, unknown> & { explanation?: string[] };
type InputField = {
  key: string;
  label: string;
  group: "direct" | "assumptions";
};

const fields: InputField[] = [
  { key: "arv", label: "ARV", group: "direct" },
  {
    key: "estimated_market_value",
    label: "Estimated market value",
    group: "direct",
  },
  { key: "outstanding_debt", label: "Outstanding debt", group: "direct" },
  { key: "repair_cost", label: "Repairs", group: "direct" },
  {
    key: "purchase_contract_price",
    label: "Purchase contract price",
    group: "direct",
  },
  {
    key: "expected_assignment_price",
    label: "Expected assignment price",
    group: "direct",
  },
  { key: "asking_price", label: "Asking price", group: "direct" },
  { key: "expected_sale_price", label: "Expected sale price", group: "direct" },
  { key: "net_profit", label: "Net profit", group: "direct" },
  {
    key: "mao_percentage",
    label: "MAO percentage (enter % points)",
    group: "assumptions",
  },
  { key: "desired_profit", label: "Desired profit", group: "assumptions" },
  {
    key: "transaction_costs",
    label: "Transaction costs",
    group: "assumptions",
  },
  { key: "holding_costs", label: "Holding costs", group: "assumptions" },
  { key: "financing_costs", label: "Financing costs", group: "assumptions" },
  { key: "other_costs", label: "Other costs", group: "assumptions" },
  {
    key: "total_invested_capital",
    label: "Total invested capital",
    group: "assumptions",
  },
];

const resultLabels: Record<string, string> = {
  arv: "ARV",
  equity: "Equity",
  mao: "MAO",
  wholesale_spread: "Wholesale spread",
  wholesale_margin: "Wholesale margin",
  flip_profit: "Flip profit",
  roi: "ROI",
  price_vs_comps: "Price vs comps",
  price_vs_arv: "Price vs ARV",
  deal_score: "Deal score",
  risk_score: "Risk score",
  classification: "Classification",
};
const percentageMetrics = new Set([
  "wholesale_margin",
  "roi",
  "price_vs_comps",
  "price_vs_arv",
]);
const currencyMetrics = new Set([
  "arv",
  "equity",
  "mao",
  "wholesale_spread",
  "flip_profit",
]);

function getOrganizationId(
  session: { user?: { app_metadata?: Record<string, unknown> } } | null
) {
  const value = session?.user?.app_metadata?.organization_id;
  return typeof value === "string" && value.length > 0 ? value : null;
}

function displayMetric(key: string, metric: Metric) {
  if (metric.value === null || metric.value === undefined)
    return metric.state ?? "UNKNOWN";
  const value = metric.value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });
  if (percentageMetrics.has(key)) return `${value}%`;
  return currencyMetrics.has(key) ? `$${value}` : value;
}

export function DealAnalysisPanel() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const calculationRevision = useRef(0);
  const requestController = useRef<AbortController | null>(null);

  useEffect(() => {
    let currentScope: string | null | undefined;
    const unsubscribe = observeSupabaseSession(session => {
      const nextScope = getSupabaseSessionScopeKey(session);
      if (nextScope === currentScope) return;
      currentScope = nextScope;
      calculationRevision.current += 1;
      requestController.current?.abort();
      requestController.current = null;
      setValues({});
      setResult(null);
      setError("");
      setLoading(false);
    });
    return () => {
      calculationRevision.current += 1;
      requestController.current?.abort();
      unsubscribe();
    };
  }, []);

  function numberValue(key: string) {
    const raw = values[key];
    if (raw === undefined || raw === "") return undefined;
    const value = Number(raw);
    if (!Number.isFinite(value))
      throw new Error(
        `${fields.find(field => field.key === key)?.label ?? key} must be a valid finite number.`
      );
    return {
      classification: "USER_INPUT",
      value,
      source: "User-entered deal analysis input",
      confidence: "USER_PROVIDED",
    };
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const requestId = ++calculationRevision.current;
    requestController.current?.abort();
    const controller = new AbortController();
    requestController.current = controller;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const client = getSupabaseBrowserClient();
      const resolvedSession = client
        ? (await client.auth.getSession()).data.session
        : null;
      if (requestId !== calculationRevision.current) return;
      const token = resolvedSession?.access_token;
      const organizationId = getOrganizationId(resolvedSession);
      if (!token) throw new Error("Sign in to calculate deal analysis.");
      if (!organizationId)
        throw new Error(
          "Your signed-in account is not assigned to an approved organization."
        );

      const payload: Record<string, unknown> = { assumptions: {} };
      for (const field of fields) {
        const value = numberValue(field.key);
        if (value) {
          const normalizedValue =
            field.key === "mao_percentage"
              ? { ...value, value: value.value / 100 }
              : value;
          if (field.group === "assumptions")
            (payload.assumptions as Record<string, unknown>)[field.key] =
              normalizedValue;
          else payload[field.key] = normalizedValue;
        }
      }
      const response = await fetch("/api/v1/deal-analysis", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Organization-Id": organizationId,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const body = await response.json().catch(() => ({}));
      if (requestId !== calculationRevision.current) return;
      if (!response.ok)
        throw new Error(
          body?.detail?.message ??
            "The deterministic analysis request could not be completed."
        );
      setResult(body as AnalysisResult);
    } catch (caught) {
      if (requestId === calculationRevision.current) {
        setError(
          caught instanceof Error
            ? caught.message
            : "The deterministic analysis request could not be completed."
        );
      }
    } finally {
      if (requestId === calculationRevision.current) {
        setLoading(false);
        if (requestController.current === controller) requestController.current = null;
      }
    }
  }

  return (
    <div className="deal-analysis-panel">
      <form onSubmit={submit}>
        <p className="analysis-note">
          Inputs are explicitly marked USER_INPUT and are not saved. Editing
          any input clears prior results; missing values remain UNKNOWN or INSUFFICIENT_DATA.
        </p>
        <div className="analysis-input-grid">
          {fields.map(field => (
            <label className="analysis-input" key={field.key}>
              <span>{field.label}</span>
              <input
                type="number"
                step="any"
                min={field.key === "mao_percentage" ? 0 : undefined}
                max={field.key === "mao_percentage" ? 100 : undefined}
                inputMode="decimal"
                value={values[field.key] ?? ""}
                onChange={event => {
                  calculationRevision.current += 1;
                  requestController.current?.abort();
                  requestController.current = null;
                  setLoading(false);
                  setResult(null);
                  setError("");
                  setValues(current => ({
                    ...current,
                    [field.key]: event.target.value,
                  }));
                }}
              />
            </label>
          ))}
        </div>
        <div className="analysis-actions">
          <button
            type="submit"
            className="button button-primary"
            disabled={loading}
          >
            {loading ? (
              <LoaderCircle size={15} className="analysis-spinner" />
            ) : null}
            {loading ? "Calculating…" : "Calculate deterministically"}
          </button>
          <span>Backend formulas only · No AI financial calculation</span>
        </div>
      </form>
      {error && (
        <div className="form-error" role="alert">
          <CircleAlert size={16} />
          <span>{error}</span>
        </div>
      )}
      {result && (
        <section className="analysis-results" aria-live="polite">
          <header>
            <h3>Deterministic results</h3>
            <span>CALCULATED BY BACKEND</span>
          </header>
          <div className="analysis-result-grid">
            {Object.entries(resultLabels).map(([key, label]) => {
              const metric = result[key] as Metric | undefined;
              if (!metric) return null;
              return (
                <article className="analysis-result-card" key={key}>
                  <span>{label}</span>
                  <strong>{displayMetric(key, metric)}</strong>
                  <small>
                    {metric.state ?? "UNKNOWN"} ·{" "}
                    {metric.classification ?? "UNKNOWN"}
                  </small>
                  {metric.reason ? (
                    <p>{metric.reason}</p>
                  ) : metric.formula ? (
                    <p>{metric.formula}</p>
                  ) : null}
                </article>
              );
            })}
          </div>
          {result.explanation && (
            <ul className="analysis-explanation">
              {result.explanation.map(line => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
