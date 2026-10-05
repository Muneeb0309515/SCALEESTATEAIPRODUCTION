import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.providers import realtyapi


def provider_record(index: int) -> dict:
    return {
        "property_id": f"prop-{index}",
        "property_type": "single_family",
        "list_price": 250000 + index,
        "status": "for_sale",
        "address": {
            "line": f"{index} Main St",
            "city": "Austin",
            "state_code": "TX",
            "postal_code": "78744",
            "latitude": 30.2,
            "longitude": -97.7,
        },
        "details": {"beds": 3, "baths": 2, "sqft": 1500},
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, **kwargs):
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, **kwargs):
        self.request = (url, kwargs)
        return FakeResponse({"searchResults": [provider_record(i) for i in range(5)], "total": 37, "nextPage": False})


class RealtyApiAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_limits_results_and_preserves_provenance(self):
        settings = SimpleNamespace(realtyapi_base_url="https://realtor.realtyapi.io", realtyapi_api_key="test-key")
        with patch.object(realtyapi, "get_settings", return_value=settings), patch.object(realtyapi.httpx, "AsyncClient", FakeAsyncClient):
            result = await realtyapi.RealtyApiAdapter().search(realtyapi.RealtySearchCriteria(location="Austin, TX", page=2, limit=3))

        self.assertEqual(len(result.results), 3)
        self.assertEqual(result.total, 37)
        self.assertTrue(result.has_next_page)
        self.assertEqual(result.results[0].source, "realtyapi")
        self.assertIsNone(result.results[0].data_updated_at)
        self.assertIsNotNone(result.results[0].source_retrieved_at)
        self.assertEqual(result.results[0].provider_property_id, "prop-0")


if __name__ == "__main__":
    unittest.main()
