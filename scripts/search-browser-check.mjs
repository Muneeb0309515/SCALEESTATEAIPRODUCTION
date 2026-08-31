import assert from "node:assert/strict";
import { chromium } from "playwright";

const baseUrl = process.env.SEARCH_PREVIEW_URL ?? "http://127.0.0.1:3000";
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH ?? "/usr/bin/chromium" });
const page = await browser.newPage();
let searchRequest;
page.on("request", (request) => {
  if (request.url().includes("/api/v1/providers/property-search")) searchRequest = request;
});
try {
  await page.goto(`${baseUrl}/search`, { waitUntil: "networkidle" });
  await page.selectOption('select[aria-label="Property category"]', "single_family");
  await page.fill('input[aria-label="Location"]', "Austin, TX");
  await page.getByRole("button", { name: "Search properties" }).click();
  const searchAlert = page.locator(".form-error[role=alert]");
  await searchAlert.waitFor({ state: "visible" });
  const alertText = await searchAlert.innerText();
  assert.match(alertText, /Sign in to an approved workspace before searching live property records/i);
  await page.getByRole("link", { name: "Review access state" }).waitFor({ state: "visible" });
  await page.getByRole("button", { name: "Search properties" }).waitFor({ state: "visible" });
  assert.equal(searchRequest, undefined, "The browser must not send a provider request without an authenticated session.");

  const providerPage = await browser.newPage();
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  assert.ok(supabaseUrl, "The browser fixture requires the public Supabase URL.");
  const storageKey = `sb-${new URL(supabaseUrl).hostname.split(".")[0]}-auth-token`;
  await providerPage.addInitScript(({ key }) => {
    window.localStorage.setItem(key, JSON.stringify({ access_token: "fixture-access-token", refresh_token: "fixture-refresh-token", expires_in: 3600, expires_at: Math.floor(Date.now() / 1000) + 3600, token_type: "bearer", user: { id: "fixture-user", aud: "authenticated", role: "authenticated", email: "fixture@example.com", app_metadata: { organization_id: "org-fixture" } } }));
  }, { key: storageKey });
  await providerPage.route("**/api/v1/providers/property-search**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [{ provider_property_id: "fixture-property-1", address: "123 Main St", city: "Austin", state: "TX", zip_code: "78744", property_type: "single_family", list_price: 275000, beds: 3, baths: 2, living_area: 1500, source: "realtyapi", data_updated_at: "2026-08-28T00:00:00Z" }],
        total: 1,
        page: 1,
        has_next_page: false,
        provider: "realtyapi",
        retrieved_at: "2026-08-28T00:00:00Z",
      }),
    });
  });
  await providerPage.goto(`${baseUrl}/search`, { waitUntil: "networkidle" });
  await providerPage.fill('input[aria-label="Location"]', "Austin, TX");
  await providerPage.getByRole("button", { name: "Search properties" }).click();
  await providerPage.getByRole("link", { name: /123 Main St/ }).waitFor({ state: "visible" });
  await providerPage.getByRole("button", { name: "Search properties" }).waitFor({ state: "visible" });
  assert.match(await providerPage.locator(".result-provenance").innerText(), /Source: realtyapi · Updated/);
  await providerPage.close();
  console.log("Browser search check passed: category filter submitted, auth-required state rendered, and provider provenance card rendered.");
} finally {
  await browser.close();
}
