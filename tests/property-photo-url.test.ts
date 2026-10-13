import { describe, expect, it } from "vitest";
import { isTrustedPropertyPhotoUrl } from "../lib/property-photo-url";

describe("property photo URL trust policy", () => {
  it("allows HTTPS images on approved Realtor, RealtyAPI, and RDCPix hosts", () => {
    expect(isTrustedPropertyPhotoUrl("https://ap.rdcpix.com/photo.jpg?size=large")).toBe(true);
    expect(isTrustedPropertyPhotoUrl("https://photos.realtor.com/photo.jpg")).toBe(true);
    expect(isTrustedPropertyPhotoUrl("https://cdn.realtyapi.io/photo.jpg")).toBe(true);
  });

  it("rejects unsafe schemes, malformed URLs, credentials, lookalike hosts, and non-default ports", () => {
    for (const value of [
      "javascript:alert(1)",
      "data:image/svg+xml,<svg/>",
      "http://ap.rdcpix.com/photo.jpg",
      "//ap.rdcpix.com/photo.jpg",
      "https:///ap.rdcpix.com/photo.jpg",
      "https:ap.rdcpix.com/photo.jpg",
      "https://rdcpix.com.attacker.example/photo.jpg",
      "https://@ap.rdcpix.com/photo.jpg",
      "https://user@ap.rdcpix.com/photo.jpg",
      "https://ap.rdcpix.com:/photo.jpg",
      "https://ap.rdcpix.com:444/photo.jpg",
      "https://ap.rdcpix.com\\@attacker.example/photo.jpg",
      " not a url ",
      null,
      42,
    ]) {
      expect(isTrustedPropertyPhotoUrl(value), String(value)).toBe(false);
    }
  });
});
