import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.core.auth import AuthenticatedIdentity
from backend.app.data import OrganizationScope
from backend.app.providers.base import CanonicalProperty
from backend.app.providers.realtyapi import RealtyApiAdapter, RealtySearchResult
from backend.tests.test_property_persistence import ConcurrentFakeClient, ConcurrentStore


def persisted_row(property_record, record_id="stored-property-1"):
    return {
        "id": record_id,
        "provider_property_id": property_record.provider_property_id,
        "provider_listing_id": property_record.provider_listing_id,
        "address": property_record.address,
        "city": property_record.city,
        "state": property_record.state,
        "zip": property_record.zip_code,
        "property_type": property_record.property_type,
        "list_price": property_record.list_price,
        "beds": property_record.beds,
        "baths": property_record.baths,
        "living_area": property_record.living_area,
        "source": property_record.source,
        "data_updated_at": property_record.data_updated_at.isoformat() if property_record.data_updated_at else None,
        "source_retrieved_at": property_record.source_retrieved_at.isoformat() if property_record.source_retrieved_at else None,
        "photos": property_record.photos,
        "provenance": {},
    }


class AuthenticatedPropertySearchTests(unittest.TestCase):
    def test_missing_organization_header_is_rejected(self):
        identity = AuthenticatedIdentity(user_id="user-1", email="owner@example.com")
        main.app.dependency_overrides[main.require_authenticated_identity] = lambda: identity
        try:
            response = TestClient(main.app).get("/api/v1/providers/property-search", params={"location": "Austin, TX"})
        finally:
            main.app.dependency_overrides.pop(main.require_authenticated_identity, None)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "ORGANIZATION_REQUIRED")

    def test_non_member_organization_is_rejected(self):
        identity = AuthenticatedIdentity(user_id="user-1", email="owner@example.com")
        main.app.dependency_overrides[main.require_authenticated_identity] = lambda: identity
        try:
            with patch("backend.app.data.scope.require_organization_member", side_effect=HTTPException(status_code=403, detail={"code": "ORGANIZATION_ACCESS_DENIED", "message": "The authenticated user is not a member of this organization."})):
                response = TestClient(main.app).get("/api/v1/providers/property-search", params={"location": "Austin, TX"}, headers={"X-Organization-Id": "org-other"})
        finally:
            main.app.dependency_overrides.pop(main.require_authenticated_identity, None)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "ORGANIZATION_ACCESS_DENIED")

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
        repository = MagicMock()
        repository.upsert_properties.return_value = [persisted_row(property_record)]
        scope = OrganizationScope(organization_id="org-1", user_id=identity.user_id)
        main.app.dependency_overrides[main.require_organization_scope] = lambda: scope
        try:
            with patch.object(main, "get_settings", return_value=settings), patch.object(main, "require_property_provider", return_value="realtyapi"), patch.object(main, "get_property_provider", return_value=adapter), patch.object(main, "OrganizationRepository", return_value=repository):
                response = TestClient(main.app).get("/api/v1/providers/property-search", params={"location": "Austin, TX", "property_type": "single_family", "limit": 1}, headers={"X-Organization-Id": "org-1"})
        finally:
            main.app.dependency_overrides.pop(main.require_organization_scope, None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["provider_property_id"], "property-1")
        self.assertEqual(response.json()["results"][0]["organization_property_id"], "stored-property-1")
        self.assertEqual(response.json()["results"][0]["source"], "realtyapi")
        repository.upsert_properties.assert_called_once_with([property_record])
        adapter.search.assert_awaited_once()
        self.assertEqual(adapter.search.await_args.args[0].property_type, "single_family")
        self.assertEqual(adapter.search.await_args.args[0].limit, 1)

    def test_concurrent_same_listing_http_requests_do_not_return_503_or_duplicate_properties(self):
        request_count = 8
        store = ConcurrentStore(request_count)
        repository = object.__new__(main.OrganizationRepository)
        repository.organization_id = "org-1"
        repository.client = ConcurrentFakeClient(store)
        scope = OrganizationScope(organization_id="org-1", user_id="user-1")
        property_record = CanonicalProperty(
            provider_property_id="racing-property-1",
            address="123 Main St, Austin, TX 78744",
            city="Austin",
            state="TX",
            zip_code="78744",
            property_type="single_family",
            list_price=275000,
            source="realtyapi",
        )
        provider_response = RealtySearchResult(
            results=[property_record], total=1, page=1, has_next_page=False,
            retrieved_at=datetime.now(timezone.utc),
        )
        adapter = RealtyApiAdapter()
        adapter.search = AsyncMock(return_value=provider_response)
        main.app.dependency_overrides[main.require_organization_scope] = lambda: scope

        def make_request():
            with TestClient(main.app) as client:
                return client.get(
                    "/api/v1/providers/property-search",
                    params={"location": "Austin, TX", "limit": 1},
                    headers={"X-Organization-Id": "org-1"},
                )

        try:
            with patch.object(main, "require_property_provider", return_value="realtyapi"), \
                 patch.object(main, "get_property_provider", return_value=adapter), \
                 patch.object(main, "OrganizationRepository", return_value=repository):
                with ThreadPoolExecutor(max_workers=request_count) as executor:
                    responses = list(executor.map(lambda _: make_request(), range(request_count)))
        finally:
            main.app.dependency_overrides.pop(main.require_organization_scope, None)

        self.assertEqual([response.status_code for response in responses], [200] * request_count)
        self.assertEqual(len(store["properties"]), 1)
        self.assertEqual(len({response.json()["results"][0]["organization_property_id"] for response in responses}), 1)

    def test_authenticated_provider_detail_reaches_property_detail_route(self):
        identity = AuthenticatedIdentity(user_id="user-1", email="owner@example.com")
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
        adapter = RealtyApiAdapter()
        adapter.details_by_address = AsyncMock(return_value=property_record)
        repository = MagicMock()
        repository.upsert_property.return_value = persisted_row(property_record)
        scope = OrganizationScope(organization_id="org-1", user_id=identity.user_id)
        main.app.dependency_overrides[main.require_organization_scope] = lambda: scope
        try:
            with patch.object(main, "require_property_provider", return_value="realtyapi"), patch.object(main, "get_property_provider", return_value=adapter), patch.object(main, "OrganizationRepository", return_value=repository):
                response = TestClient(main.app).get("/api/v1/providers/property-detail", params={"address": property_record.address}, headers={"X-Organization-Id": "org-1"})
        finally:
            main.app.dependency_overrides.pop(main.require_organization_scope, None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider_property_id"], "property-1")
        self.assertEqual(response.json()["organization_property_id"], "stored-property-1")
        self.assertEqual(response.json()["source"], "realtyapi")
        repository.upsert_property.assert_called_once_with(property_record)
        adapter.details_by_address.assert_awaited_once_with(property_record.address)

    def test_persisted_property_list_returns_canonical_contract(self):
        scope = OrganizationScope(organization_id="org-1", user_id="user-1")
        repository = MagicMock()
        repository.list.return_value = [{"id": "stored-property-1", "organization_id": "org-1", "address": "123 Main St", "city": "Austin", "state": "TX", "zip": "78744", "property_type": None, "source": "realtyapi", "provenance": {"list_price": {"classification": "UNKNOWN"}}, "photos": [], "data_updated_at": None, "source_retrieved_at": "2026-10-04T00:00:00Z", "last_seen_at": "2026-10-04T00:00:00Z"}]
        main.app.dependency_overrides[main.require_organization_scope] = lambda: scope
        try:
            with patch.object(main, "OrganizationRepository", return_value=repository):
                response = TestClient(main.app).get("/api/v1/properties", headers={"X-Organization-Id": "org-1"})
        finally:
            main.app.dependency_overrides.pop(main.require_organization_scope, None)
        self.assertEqual(response.status_code, 200)
        body = response.json()[0]
        self.assertEqual(body["organization_property_id"], "stored-property-1")
        self.assertEqual(body["zip_code"], "78744")
        self.assertNotIn("zip", body)


if __name__ == "__main__":
    unittest.main()
