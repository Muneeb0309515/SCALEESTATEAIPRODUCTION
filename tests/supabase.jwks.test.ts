import { describe, expect, it } from "vitest";

type Jwk = { kid?: string; kty?: string; alg?: string };
type JwkSet = { keys?: Jwk[] };

describe("Supabase JWKS configuration", () => {
  it("accepts public ES256 signing metadata for the approved project", async () => {
    const raw = process.env.SUPABASE_JWKS_JSON?.trim();
    const projectUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    expect(raw).toBeTruthy();
    expect(projectUrl).toMatch(/^https:\/\/[^/]+\.supabase\.co$/);

    const configured: JwkSet = raw?.startsWith("https://")
      ? await (await fetch(raw)).json() as JwkSet
      : JSON.parse(raw as string) as JwkSet;
    expect(configured.keys?.length).toBeGreaterThan(0);
    expect(configured.keys?.some((key) => key.kty === "EC" && key.alg === "ES256" && key.kid)).toBe(true);

    const response = await fetch(`${projectUrl}/auth/v1/.well-known/jwks.json`);
    expect(response.status).toBe(200);
    const remote = await response.json() as JwkSet;
    const remoteKids = new Set((remote.keys ?? []).map((key) => key.kid));
    expect((configured.keys ?? []).some((key) => remoteKids.has(key.kid))).toBe(true);
  });
});
