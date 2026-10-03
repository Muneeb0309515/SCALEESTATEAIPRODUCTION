import { describe, expect, it } from "vitest";

async function callRapidApi(host: string, apiKey: string, path: string) {
  const response = await fetch(`https://${host}${path}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-RapidAPI-Key": apiKey,
      "X-RapidAPI-Host": host,
    },
  });

  const contentType = response.headers.get("content-type") ?? "";
  let dataAccessible = false;
  if (contentType.includes("application/json")) {
    const payload: unknown = await response.json();
    dataAccessible = payload !== null && payload !== undefined;
  } else {
    const body = await response.text();
    dataAccessible = body.length > 0;
  }

  return { status: response.status, dataAccessible };
}

describe("RapidAPI credentials", () => {
  it("validates the Red US Real Estate Listings endpoint", async () => {
    const apiKey = process.env.RAPIDAPI_KEY_RED;
    const host = "red-us-real-estate-listings.p.rapidapi.com";
    expect(apiKey, "RAPIDAPI_KEY_RED must be configured").toBeTruthy();

    const result = await callRapidApi(host, apiKey!, "/housingMarketDemand?id=4_325");
    expect(result.status).toBe(200);
    expect(result.dataAccessible).toBe(true);
  }, 30_000);

  it("validates the US Real Estate Listings endpoint", async () => {
    const apiKey = process.env.RAPIDAPI_KEY_LISTINGS;
    const host = "us-real-estate-listings.p.rapidapi.com";
    expect(apiKey, "RAPIDAPI_KEY_LISTINGS must be configured").toBeTruthy();

    const result = await callRapidApi(host, apiKey!, "/popularity?property_id=0&listing_id=0");
    expect(result.status).toBe(200);
    expect(result.dataAccessible).toBe(true);
  }, 30_000);
});
