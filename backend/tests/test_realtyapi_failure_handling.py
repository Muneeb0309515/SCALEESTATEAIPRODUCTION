import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from backend.app.providers import realtyapi


class Response:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


class Client:
    response = Response({"searchResults": [], "total": 0})

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, *_args, **_kwargs):
        return self.response


class RealtyApiFailureTests(unittest.IsolatedAsyncioTestCase):
    settings = SimpleNamespace(realtyapi_base_url="https://realtor.realtyapi.io", realtyapi_api_key="test-key")

    async def call_search(self):
        with patch.object(realtyapi, "get_settings", return_value=self.settings), patch.object(realtyapi.httpx, "AsyncClient", Client):
            return await realtyapi.RealtyApiAdapter().search(realtyapi.RealtySearchCriteria(location="Travis County, TX", limit=1))

    async def test_empty_result_is_a_valid_empty_result(self):
        Client.response = Response({"searchResults": [], "total": 0})
        result = await self.call_search()
        self.assertEqual(result.results, [])
        self.assertEqual(result.total, 0)

    async def test_malformed_payload_fails_with_value_error(self):
        Client.response = Response(["not", "an", "object"])
        with self.assertRaisesRegex(ValueError, "must be an object"):
            await self.call_search()

    async def test_malformed_result_collection_fails_with_value_error(self):
        Client.response = Response({"searchResults": {"unexpected": True}})
        with self.assertRaisesRegex(ValueError, "must be a list"):
            await self.call_search()

    async def test_missing_required_address_fields_is_not_normalized(self):
        Client.response = Response({"searchResults": [{"property_id": "missing-address"}], "total": 1})
        result = await self.call_search()
        self.assertEqual(result.results, [])

    async def test_timeout_is_propagated_as_http_error_for_route_mapping(self):
        Client.response = Response(error=httpx.ReadTimeout("provider timeout"))
        with self.assertRaises(httpx.ReadTimeout):
            await self.call_search()

    async def test_rate_limit_is_propagated_as_http_error_for_route_mapping(self):
        Client.response = Response(error=httpx.HTTPStatusError("rate limited", request=httpx.Request("GET", "https://example.test"), response=httpx.Response(429)))
        with self.assertRaises(httpx.HTTPStatusError):
            await self.call_search()


if __name__ == "__main__":
    unittest.main()
