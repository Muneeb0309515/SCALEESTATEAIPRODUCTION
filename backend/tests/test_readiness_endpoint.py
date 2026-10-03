import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import main


class ReadinessEndpointTests(unittest.TestCase):
    def test_endpoint_returns_statuses_without_credentials(self):
        with patch.object(main, "integration_readiness", return_value={
            "realtyapi": "REALTYAPI_NOT_CONFIGURED",
            "supabase": "SUPABASE_NOT_CONFIGURED",
        }):
            response = TestClient(main.app).get("/api/v1/integrations/readiness")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "realtyapi": "REALTYAPI_NOT_CONFIGURED",
            "supabase": "SUPABASE_NOT_CONFIGURED",
        })
        self.assertNotIn("key", response.text.lower())
        self.assertNotIn("token", response.text.lower())


if __name__ == "__main__":
    unittest.main()
