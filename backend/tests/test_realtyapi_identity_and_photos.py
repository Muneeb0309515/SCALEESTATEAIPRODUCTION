import unittest
from datetime import datetime, timezone

from backend.app.providers.realtyapi import RealtyApiAdapter


class RealtyApiIdentityAndPhotoTests(unittest.TestCase):
    def test_normalization_preserves_listing_identity_and_string_photos(self):
        record = {
            "property_id": "property-1",
            "listing_id": "listing-1",
            "address": {"line": "1 Main St", "city": "Austin", "state_code": "TX", "postal_code": "78744"},
            "details": {"beds": 3, "baths": "2", "sqft": 1500},
            "photos": ["https://example.test/one.jpg", "https://example.test/two.jpg"],
        }
        normalized = RealtyApiAdapter._normalize(record)
        assert normalized is not None
        self.assertEqual(normalized.provider_property_id, "property-1")
        self.assertEqual(normalized.provider_listing_id, "listing-1")
        self.assertEqual(normalized.photos, ["https://example.test/one.jpg", "https://example.test/two.jpg"])
        self.assertEqual(normalized.source, "realtyapi")
        self.assertIsInstance(normalized.data_updated_at, datetime)

    def test_normalization_accepts_photo_objects_and_keeps_missing_values_unknown(self):
        record = {
            "property_id": "property-2",
            "address": {"line": "2 Main St", "city": "Austin", "state_code": "TX", "postal_code": "78744"},
            "details": {"baths": "not-a-number"},
            "photos": [{"href": "https://example.test/object.jpg"}, {"url": "https://example.test/url.jpg"}],
        }
        normalized = RealtyApiAdapter._normalize(record)
        assert normalized is not None
        self.assertIsNone(normalized.provider_listing_id)
        self.assertEqual(normalized.photos, ["https://example.test/object.jpg", "https://example.test/url.jpg"])
        self.assertIsNone(normalized.baths)
        self.assertIsNone(normalized.list_price)
        self.assertEqual(normalized.property_type, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
