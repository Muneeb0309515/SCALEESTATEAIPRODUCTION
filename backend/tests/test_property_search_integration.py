import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app import main
from backend.app.core.auth import AuthenticatedIdentity
from backend.app.providers.base import CanonicalProperty
from backend.app.providers.realtyapi import RealtyApiAdapter, RealtySearchResult


class AuthenticatedPropertySearchTests(unittest.TestCase):
    def test_authenticated_provider_result_reaches_search_route(self):
        identity = AuthenticatedIdentity(user_id="user-1", email="owner@example.com")
        settings = SimpleNamespace(realtyapi_base_url="https://realtor.realtyapi.io", realtyapi_api_key="test-key")
        property_record = CanonicalProperty(
            provider_property_id="property-1",
            address="123 Main St, Austin, TX 78744",
            city="Austin",
            state="TX",
            zip_code="78744",
            property_type="single_family",
            list_price=275000,
            beds=3,
            baths=2,
            living_area=1500,
            source="realtyapi",
            data_updated_at=datetime.now(timezone.utc),
        )
        provider_response = RealtySearchResult(results=[property_record], total=1, page=1, has_next_page=False, retrieved_at=datetime.now(timezone.utc))
        adapter = RealtyApiAdapter()
        adapter.search = AsyncMock(return_value=provider_response)
        main.app.dependency_overrides[main.require_authenticated_identity] = lambda: identity
        try:
            with patch.object(main, "get_settings", return_value=settings), patch.object(main, "require_property_provider", return_value="realtyapi"), patch.object(main, "get_property_provider", return_value=adapter):
                response = TestClient(main.app).get("/api/v1/providers/property-search", params={"location": "Austin, TX", "property_type": "single_family", "limit": 1})
        finally:
            main.app.dependency_overrides.pop(main.require_authenticated_identity, None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["provider_property_id"], "property-1")
        self.assertEqual(response.json()["results"][0]["source"], "realtyapi")
        adapter.search.assert_awaited_once()
        self.assertEqual(adapter.search.await_args.args[0].property_type, "single_family")
        self.assertEqual(adapter.search.await_args.args[0].limit, 1)


if __name__ == "__main__":
    unittest.main()
