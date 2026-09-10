"use client";

import { FormEvent, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";

export function ReviewableAiDraft() {
  const [facts, setFacts] = useState("Property address: verified by RealtyAPI.io");
  const [instruction, setInstruction] = useState("Ask whether the owner would consider a conversation.");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function createDraft(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setDraft("");
    const verifiedFacts = facts.split("\n").map((value, index) => ({ field: `Verified fact ${index + 1}`, value: value.trim(), source: "RealtyAPI.io", confidence: "VERIFIED" }));
    try {
      const response = await fetch("/api/v1/ai/drafts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ draft_type: "seller_outreach", verified_facts: verifiedFacts, user_instruction: instruction }) });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail?.message ?? "AI drafting is unavailable.");
      setDraft(body.content ?? "");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AI drafting is unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return <form className="ai-draft-form" onSubmit={createDraft}><div className="ai-form-head"><Sparkles size={18} /><div><strong>Verified context in. Reviewable draft out.</strong><p>Every line must be supported by a source-backed fact. Nothing is sent automatically.</p></div></div><label className="ai-field"><span>Verified facts only</span><textarea value={facts} onChange={(event) => setFacts(event.target.value)} rows={3} maxLength={3000} /></label><label className="ai-field"><span>User instruction</span><input value={instruction} onChange={(event) => setInstruction(event.target.value)} maxLength={1000} /></label><button className="button button-secondary full" type="submit" disabled={loading || !facts.trim()}>{loading ? <><Loader2 size={15} className="spin" /> Drafting…</> : <><Sparkles size={15} /> Prepare reviewable draft</>}</button>{error && <div className="ai-feedback error" role="alert"><AlertCircle size={15} />{error}</div>}{draft && <div className="ai-result"><div className="ai-result-label"><CheckCircle2 size={15} /> AI-generated draft · user review required</div><p>{draft}</p><small>Allowed context: verified property and owner facts only. Review and edit before use.</small></div>}</form>;
}
