import os
import unittest
from backend.app.services.availability import IntegrationUnavailable, require_property_provider


class AvailabilityTests(unittest.TestCase):
    def test_property_provider_fails_closed_when_unconfigured(self):
        old_provider = os.environ.pop("PROPERTY_DATA_PROVIDER", None)
        old_key = os.environ.pop("PROPERTY_DATA_API_KEY", None)
        try:
            with self.assertRaises(IntegrationUnavailable) as error:
                require_property_provider()
            self.assertEqual(error.exception.code, "CONFIGURATION_REQUIRED")
        finally:
            if old_provider is not None:
                os.environ["PROPERTY_DATA_PROVIDER"] = old_provider
            if old_key is not None:
                os.environ["PROPERTY_DATA_API_KEY"] = old_key

if __name__ == "__main__": unittest.main()
