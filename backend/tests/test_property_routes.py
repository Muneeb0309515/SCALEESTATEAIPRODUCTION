import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class PropertyRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_market_search_is_not_available_without_authenticated_validated_context(self):
        with patch("backend.app.core.auth.get_settings", return_value=SimpleNamespace(has_project_supabase_connection=False)):
            response = self.client.get("/api/v1/search-us-market?city=Atlanta&state=GA")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "CONFIGURATION_REQUIRED")

    def test_saved_search_and_property_routes_require_scope(self):
        with patch("backend.app.core.auth.get_settings", return_value=SimpleNamespace(has_project_supabase_connection=False)):
            for path in ("/api/v1/saved-searches", "/api/v1/properties", "/api/v1/properties/no-record", "/api/v1/providers/property-search"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 503)

    def test_activated_market_search_requires_bearer_token(self):
        with patch("backend.app.core.auth.get_settings", return_value=SimpleNamespace(has_project_supabase_connection=True)):
            response = self.client.get("/api/v1/search-us-market?city=Atlanta&state=GA")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "AUTHENTICATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
