# Property Photo URL Trust Policy

## Approved source hosts

Property-photo URLs are accepted only when they use HTTPS and the normalized host is one of these roots or a subdomain:

- `rdcpix.com` — includes common Realtor image hosts such as `ap.rdcpix.com`.
- `realtor.com`.
- `realtyapi.io`.

The allowlist is an application policy, not a claim that RealtyAPI publishes a fixed exhaustive list of image hosts. The official [RealtyAPI Realtor API page](https://www.realtyapi.io/api/realtor) describes photo fields in property results but does not document a fixed photo-host list; its [documentation introduction](https://www.realtyapi.io/docs/introduction) likewise does not specify image-host or redirect guarantees. Preserve representative, non-secret provider response fixtures when a new legitimate host needs to be considered, and review/test any allowlist expansion before merging.

## Validation rules

The backend normalizer and canonical property response filter both `primary_photo` and `photos`. The browser performs the same host check before creating an image element, so legacy database values are not trusted merely because they were persisted earlier.

A photo URL must:

- be a well-formed absolute URL with the `https` scheme;
- use an allowlisted host (exact root or a subdomain boundary match);
- have no username/password, malformed port, or non-default port (only implicit HTTPS/443 is accepted); and
- contain no whitespace/control characters or backslashes and be no longer than 2,048 characters.

Relative URLs, protocol-relative URLs, `http:`, `javascript:`, `data:`, IP literals, localhost, lookalike suffixes such as `rdcpix.com.attacker.example`, and credential-bearing URLs are rejected. Signed query strings are preserved.

## Browser privacy and redirects

The detail page uses a native lazy-loaded `<img>` with `referrerPolicy="no-referrer"`, preventing the page URL or its query parameters from being sent as the `Referer` header to the image host. It does not request arbitrary listing links as images. A direct third-party image request still reveals the viewer's network address to the approved host.

Browsers follow HTTP redirects issued by an approved image host. The frontend cannot reliably inspect/deny every redirect hop while using a native `<img>`; the allowlist validates the initial URL, not the ultimate response host. Do not add a host known to redirect photo requests to untrusted destinations. If a future requirement demands redirect-chain enforcement or hides viewer IP addresses, first design a dedicated image proxy with strict DNS/IP, redirect, size, MIME-type, timeout, and cache controls; no such proxy is implemented here.
