const TRUSTED_PROPERTY_PHOTO_DOMAINS = ["rdcpix.com", "realtor.com", "realtyapi.io"] as const;

export function isTrustedPropertyPhotoUrl(candidate: unknown): candidate is string {
  if (typeof candidate !== "string" || candidate.length === 0 || candidate.length > 2048) return false;
  if (candidate !== candidate.trim() || /[\s\\\u0000-\u001f\u007f]/u.test(candidate)) return false;
  if (!/^https:\/\//iu.test(candidate)) return false;
  const authority = candidate.slice(8).split(/[/?#]/u, 1)[0];
  if (!authority || authority.includes("@") || authority.startsWith("/") || authority.endsWith(":")) return false;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return false;
  }

  if (parsed.protocol !== "https:" || parsed.username || parsed.password) return false;
  if (parsed.port !== "" && parsed.port !== "443") return false;
  const host = parsed.hostname.toLowerCase().replace(/\.$/u, "");
  return TRUSTED_PROPERTY_PHOTO_DOMAINS.some(domain => host === domain || host.endsWith(`.${domain}`));
}
