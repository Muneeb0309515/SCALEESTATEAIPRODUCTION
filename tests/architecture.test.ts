import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("approved SCALEESTATE architecture", () => {
  it("retains the Next.js app, FastAPI service, deterministic engine, and PostgreSQL migration", () => {
    ["app/layout.tsx", "backend/app/main.py", "backend/app/deal_engine/engine.py", "backend/migrations/001_initial_schema.sql", "docs/DETERMINISTIC_DEAL_ANALYSIS_ENGINE.md"].forEach((path) => expect(existsSync(path), `${path} must exist`).toBe(true));
  });
  it("does not permit AI drafts to become a financial calculation path", () => {
    const source = readFileSync("backend/app/main.py", "utf8");
    expect(source).toContain("Never add facts");
    expect(source).toContain("Do not calculate financial metrics");
    expect(source).toContain("user-reviewable draft");
  });
  it("keeps property search filters functional through the preview proxy", () => {
    const search = readFileSync("components/LivePropertySearch.tsx", "utf8");
    const nextConfig = readFileSync("next.config.ts", "utf8");
    expect(search).toContain("Property category");
    expect(search).toContain('params.set("property_type", propertyType)');
    expect(search).toContain('params.set("status", status)');
    expect(nextConfig).toContain("3000-iz9chabu4d2hf544lzxnj-e1a973e9.us3.manus.computer");
  });
  it("keeps property actions and CRM handoff routes connected", () => {
    const intelligence = readFileSync("components/PropertyIntelligenceLive.tsx", "utf8");
    const dealWorkspace = readFileSync("components/DealWorkspaceLive.tsx", "utf8");
    const api = readFileSync("backend/app/main.py", "utf8");
    expect(existsSync("app/(workspace)/properties/[propertyId]/page.tsx")).toBe(true);
    expect(existsSync("app/(workspace)/deals/[dealId]/page.tsx")).toBe(true);
    ["Owner details", "Comparable sales", "Map", "Deal underwriting", "/api/v1/underwriting/handoff"].forEach((label) => expect(intelligence).toContain(label));
    expect(api).toContain('@app.get("/api/v1/deals/{deal_id}")');
    expect(api).toContain('@app.post("/api/v1/deals/{deal_id}/match-buyers")');
    expect(dealWorkspace).toContain("Preview");
    expect(dealWorkspace).toContain("Under Contract");
  });
});
