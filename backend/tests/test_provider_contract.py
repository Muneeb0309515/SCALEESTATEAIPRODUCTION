import unittest
from datetime import datetime, timezone
from backend.app.providers.base import CanonicalProperty
from backend.app.providers.realtyapi import RealtyApiAdapter


class ProviderContractTests(unittest.TestCase):
    def test_normalized_property_allows_unknown_provider_update_time(self):
        record = CanonicalProperty(provider_property_id="p1", address="1 Main", city="Atlanta", state="GA", zip_code="30303", property_type="single_family", source="realtyapi")
        self.assertEqual(record.source, "realtyapi")
        self.assertIsNone(record.data_updated_at)

    def test_realtyapi_rejects_record_without_provider_identity(self):
        with self.assertRaisesRegex(ValueError, "missing property_id and listing_id"):
            RealtyApiAdapter._normalize({
                "address": {"line": "1 Main", "city": "Austin", "state_code": "TX", "postal_code": "78744"},
                "details": {},
            })

if __name__ == "__main__": unittest.main()
