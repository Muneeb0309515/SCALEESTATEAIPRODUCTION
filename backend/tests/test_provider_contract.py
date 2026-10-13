import unittest
from pydantic import ValidationError
from backend.app.providers.base import CanonicalProperty


class ProviderContractTests(unittest.TestCase):
    def test_normalized_property_allows_unknown_provider_update_time(self):
        record = CanonicalProperty(provider_property_id="p1", address="1 Main", city="Atlanta", state="GA", zip_code="30303", property_type="single_family", source="realtyapi")
        self.assertEqual(record.source, "realtyapi")
        self.assertIsNone(record.data_updated_at)
        with self.assertRaises(ValidationError):
            CanonicalProperty(provider_property_id="p1", address="1 Main", city="Atlanta", state="GA", zip_code="30303", property_type="single_family", source="unknown")

if __name__ == "__main__": unittest.main()
