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
    expect(nextConfig).toContain("3000-ifk2c0egk8r030vh4b39k-2c723fe6.us1.manus.computer");
  });
  it("guards search resume and duplicate submissions", () => {
    const search = readFileSync("components/LivePropertySearch.tsx", "utf8");
    const styles = readFileSync("app/globals.css", "utf8");
    expect(search).toContain("searchRequestInFlight");
    expect(search).toContain("event?.stopPropagation()");
    expect(search).toContain('role="search"');
    expect(search).toContain('type="button" onClick={() => void submit(undefined, 1)}');
    expect(search).toContain("PropertyResultsSkeleton");
    expect(search).toContain("Loading results…");
    expect(styles).toContain("search-shimmer");
    expect(styles).toContain("prefers-reduced-motion:reduce");
    expect(search).toContain('params.delete("resume")');
    expect(search).toContain("window.history.replaceState");
  });
  it("keeps workspace sign-out wired to Supabase session cleanup", () => {
    const shell = readFileSync("components/WorkspaceShell.tsx", "utf8");
    expect(shell).toContain("client.auth.signOut()");
    expect(shell).toContain("localStorage.removeItem");
    expect(shell).toContain('window.location.assign("/sign-in")');
    expect(shell).toContain('aria-label="Sign out of workspace"');
  });
  it("preserves search context through the direct sign-in handoff", () => {
    const search = readFileSync("components/LivePropertySearch.tsx", "utf8");
    const signInPage = readFileSync("app/sign-in/page.tsx", "utf8");
    const signInForm = readFileSync("app/sign-in/SignInForm.tsx", "utf8");
    expect(search).toContain("buildSearchReturnPath");
    expect(search).toContain("Sign in to continue");
    expect(search).toContain("/sign-in?next=");
    expect(signInPage).toContain("nextPath");
    expect(signInPage).toContain("!requestedNext.startsWith(\"//\")");
    expect(signInForm).toContain("window.location.assign(redirectRef.current)");
  });
});
