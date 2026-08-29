import { describe, expect, it } from "vitest";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

describe("Supabase browser auth configuration", () => {
  it("accepts the configured public key for Auth settings", async () => {
    expect(supabaseUrl, "NEXT_PUBLIC_SUPABASE_URL must be configured").toMatch(/^https:\/\/[^/]+\.supabase\.co$/);
    expect(supabaseAnonKey, "NEXT_PUBLIC_SUPABASE_ANON_KEY must be configured").toBeTruthy();

    const response = await fetch(`${supabaseUrl}/auth/v1/settings`, {
      headers: {
        apikey: supabaseAnonKey!,
        Authorization: `Bearer ${supabaseAnonKey!}`,
      },
    });

    expect(response.ok, `Supabase Auth settings returned ${response.status}`).toBe(true);
  }, 15000);
});
