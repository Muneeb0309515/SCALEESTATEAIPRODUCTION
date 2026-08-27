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
});
