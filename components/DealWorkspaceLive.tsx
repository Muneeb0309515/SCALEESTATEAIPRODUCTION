import Link from "next/link";
import { Clock3, FileLock2, ShieldCheck, UserRoundCheck } from "lucide-react";
import { DealAnalysisPanel } from "@/components/DealAnalysisPanel";

export function DealWorkspaceLive({ dealId }: { dealId: string }) {
  return (
    <>
      <header className="screen-header">
        <div>
          <p className="eyebrow">Deal workspace</p>
          <h1>Deterministic deal analysis</h1>
          <p>
            Deal reference: {dealId}. Inputs are temporary until an
            organization-scoped deal record is available.
          </p>
        </div>
        <Link href="/deals" className="button button-secondary">
          Back to pipeline
        </Link>
      </header>
      <div className="status-banner">
        <ShieldCheck size={18} />
        <p>
          <strong>Stateless analysis mode.</strong> Calculations run through the
          authenticated backend engine. No deal or analysis snapshot is saved in
          this workflow.
        </p>
        <span>DETERMINISTIC</span>
      </div>
      <div className="deal-columns">
        <div>
          <section className="panel">
            <header className="panel-heading">
              <div>
                <h2>Deal assumptions and results</h2>
                <p>
                  Enter known values only. Missing inputs remain UNKNOWN or
                  INSUFFICIENT_DATA; AI does not calculate financial results.
                </p>
              </div>
            </header>
            <DealAnalysisPanel />
          </section>
          <section className="panel">
            <header className="panel-heading">
              <div>
                <h2>Activity timeline</h2>
                <p>
                  Auditable events are shown only after organization-scoped
                  persistence is enabled.
                </p>
              </div>
            </header>
            <div className="empty-state">
              <span className="empty-icon">
                <Clock3 size={22} />
              </span>
              <h3>No saved events</h3>
              <p>
                Stateless calculations are not persisted and do not create an
                audit record.
              </p>
            </div>
          </section>
        </div>
        <aside className="deal-side">
          <section className="panel">
            <header className="panel-heading">
              <div>
                <h2>Under-contract controls</h2>
                <p>Critical events remain locked.</p>
              </div>
            </header>
            <div className="locked-block">
              <FileLock2 size={23} />
              <strong>Snapshot not created</strong>
              <p>
                A persisted deal, verified contract inputs, and approved
                workflow transition are required before freezing analysis.
              </p>
            </div>
          </section>
          <section className="panel">
            <header className="panel-heading">
              <div>
                <h2>Buyer matching</h2>
                <p>Deterministic ranked shortlist</p>
              </div>
            </header>
            <div className="empty-state">
              <span className="empty-icon">
                <UserRoundCheck size={22} />
              </span>
              <h3>Awaiting contract event</h3>
              <p>
                Buyer matching remains unavailable until a persisted
                under-contract deal exists.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}
