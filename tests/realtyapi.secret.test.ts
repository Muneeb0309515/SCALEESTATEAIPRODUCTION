import { describe, expect, it } from "vitest";

describe("RealtyAPI.io credential", () => {
  it("is accepted by the configured read-only health endpoint", async () => {
    const apiKey = process.env.REALTYAPI_API_KEY;
    const baseUrl = process.env.REALTYAPI_BASE_URL;
    expect(process.env.PROPERTY_DATA_PROVIDER).toBe("realtyapi");
    expect(apiKey, "REALTYAPI_API_KEY must be configured").toBeTruthy();
    expect(baseUrl, "REALTYAPI_BASE_URL must be configured").toBeTruthy();
    const endpoint = `${baseUrl}/details/byaddress?address=9504%20Quail%20Village%20Ln%2C%20Austin%2C%20TX%2078758`;
    const response = await fetch(endpoint, {
      method: "GET",
      headers: { "x-realtyapi-key": apiKey! },
    });
    expect([200, 404]).toContain(response.status);
  }, 30_000);
});
