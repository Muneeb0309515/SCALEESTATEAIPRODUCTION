import { describe, expect, it } from "vitest";

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

describe("Supabase server configuration", () => {
  it("authenticates a lightweight settings request without exposing credentials", async () => {
    expect(supabaseUrl, "SUPABASE_URL must be configured").toMatch(/^https:\/\//);
    expect(supabaseKey, "SUPABASE_KEY must be configured").toBeTruthy();

    const response = await fetch(`${supabaseUrl}/auth/v1/settings`, {
      headers: {
        apikey: supabaseKey!,
        Authorization: `Bearer ${supabaseKey!}`,
      },
    });

    expect(response.ok, `Supabase settings request failed with ${response.status}`).toBe(true);
  });
});
