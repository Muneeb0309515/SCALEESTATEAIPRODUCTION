import { describe, expect, it } from "vitest";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseSessionScopeKey } from "../lib/supabase-browser";

function session(userId: string, organizationId: string | undefined, token = "token"): Session {
  return {
    access_token: token,
    refresh_token: "refresh",
    expires_in: 3600,
    token_type: "bearer",
    user: {
      id: userId,
      app_metadata: organizationId ? { organization_id: organizationId } : {},
    },
  } as Session;
}

describe("Supabase session data scope", () => {
  it("is stable across token refresh for the same user and organization", () => {
    expect(getSupabaseSessionScopeKey(session("user-a", "org-a", "old-token")))
      .toBe(getSupabaseSessionScopeKey(session("user-a", "org-a", "new-token")));
  });

  it("changes when either the account or organization changes", () => {
    const initial = getSupabaseSessionScopeKey(session("user-a", "org-a"));
    expect(getSupabaseSessionScopeKey(session("user-b", "org-a"))).not.toBe(initial);
    expect(getSupabaseSessionScopeKey(session("user-a", "org-b"))).not.toBe(initial);
  });

  it("returns null when no authenticated bearer session exists", () => {
    expect(getSupabaseSessionScopeKey(null)).toBeNull();
    expect(getSupabaseSessionScopeKey({ ...session("user-a", "org-a"), access_token: "" } as Session)).toBeNull();
  });
});
