"""Strict URL validation for provider-hosted property photos."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit


TRUSTED_PROPERTY_PHOTO_DOMAINS = frozenset({"rdcpix.com", "realtor.com", "realtyapi.io"})


def sanitize_provider_photo_url(candidate: Any) -> str | None:
    """Return an HTTPS URL on an approved provider image domain, else None.

    Only the initial URL host is validated; browser image redirects are handled
    separately in the UI policy and never receive a Referer header.
    """
    if not isinstance(candidate, str) or not candidate or len(candidate) > 2048:
        return None
    if candidate != candidate.strip() or any(char.isspace() or ord(char) < 0x20 or ord(char) == 0x7F for char in candidate):
        return None
    if "\\" in candidate:
        return None

    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    if parsed.scheme.lower() != "https" or not hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.netloc.endswith(":"):
        return None
    if port not in (None, 443):
        return None

    host = hostname.casefold().rstrip(".")
    if not any(host == domain or host.endswith(f".{domain}") for domain in TRUSTED_PROPERTY_PHOTO_DOMAINS):
        return None
    return candidate


def sanitize_provider_photo_urls(candidates: Any) -> list[str]:
    """Keep distinct, trusted provider photos from a JSON/API value."""
    if not isinstance(candidates, list):
        return []

    safe_urls: list[str] = []
    for candidate in candidates:
        safe_url = sanitize_provider_photo_url(candidate)
        if safe_url and safe_url not in safe_urls:
            safe_urls.append(safe_url)
    return safe_urls
