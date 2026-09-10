import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from backend.app.providers.base import CanonicalProperty


class ProviderContractTests(unittest.TestCase):
    def test_normalized_property_requires_provider_origin_and_update_time(self):
        record = CanonicalProperty(provider_property_id="p1", address="1 Main", city="Atlanta", state="GA", zip_code="30303", property_type="single_family", source="rapidapi", data_updated_at=datetime.now(timezone.utc))
        self.assertEqual(record.source, "rapidapi")
        with self.assertRaises(ValidationError):
            CanonicalProperty(provider_property_id="p1", address="1 Main", city="Atlanta", state="GA", zip_code="30303", property_type="single_family", source="rapidapi")

if __name__ == "__main__": unittest.main()
