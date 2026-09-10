import os
import unittest

from backend.app.core.config import get_settings
from backend.app.services.availability import integration_readiness


class ReadinessTests(unittest.TestCase):
    NAMES = (
        "PROPERTY_DATA_PROVIDER",
        "REALTYAPI_API_KEY",
        "REALTYAPI_BASE_URL",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_PROJECT_VALIDATED",
    )

    def setUp(self):
        self.original = {name: os.environ.get(name) for name in self.NAMES}
        get_settings.cache_clear()

    def tearDown(self):
        for name, value in self.original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        get_settings.cache_clear()

    def clear_names(self):
        for name in self.NAMES:
            os.environ.pop(name, None)

    def test_missing_configuration_returns_safe_statuses_only(self):
        self.clear_names()
        readiness = integration_readiness()
        self.assertEqual(readiness, {
            "realtyapi": "REALTYAPI_NOT_CONFIGURED",
            "supabase": "SUPABASE_NOT_CONFIGURED",
        })
        self.assertTrue(all(value.endswith(("CONFIGURED", "NOT_CONFIGURED")) for value in readiness.values()))

    def test_complete_configuration_returns_configured_statuses_without_values(self):
        self.clear_names()
        os.environ.update({
            "PROPERTY_DATA_PROVIDER": "realtyapi",
            "REALTYAPI_API_KEY": "test-secret-that-must-not-be-returned",
            "REALTYAPI_BASE_URL": "https://realtor.realtyapi.io",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-server-key-that-must-not-be-returned",
            "SUPABASE_PROJECT_VALIDATED": "true",
        })
        get_settings.cache_clear()
        readiness = integration_readiness()
        self.assertEqual(readiness, {
            "realtyapi": "REALTYAPI_CONFIGURED",
            "supabase": "SUPABASE_CONFIGURED",
        })
        serialized = repr(readiness)
        self.assertNotIn("test-secret", serialized)
        self.assertNotIn("test-server-key", serialized)

    def test_realtyapi_is_not_ready_without_explicit_provider_selector(self):
        self.clear_names()
        os.environ.update({
            "REALTYAPI_API_KEY": "test-secret",
            "REALTYAPI_BASE_URL": "https://realtor.realtyapi.io",
        })
        get_settings.cache_clear()
        self.assertEqual(integration_readiness()["realtyapi"], "REALTYAPI_NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
