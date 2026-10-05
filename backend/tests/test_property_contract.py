import unittest

from backend.app.data.property_contract import canonical_property_response


class PropertyContractTests(unittest.TestCase):
    def test_persisted_row_uses_canonical_field_names_and_metadata(self):
        result = canonical_property_response({
            "id": "org-property-1",
            "provider_property_id": "provider-1",
            "provider_listing_id": None,
            "address": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip": "78744",
            "property_type": None,
            "list_price": None,
            "estimated_value": None,
            "source": "realtyapi",
            "provenance": {"list_price": {"classification": "UNKNOWN"}},
            "source_retrieved_at": "2026-10-04T00:00:00Z",
            "data_updated_at": None,
            "last_seen_at": "2026-10-04T00:00:00Z",
        })
        self.assertEqual(result["organization_property_id"], "org-property-1")
        self.assertEqual(result["zip_code"], "78744")
        self.assertNotIn("zip", result)
        self.assertIsNone(result["estimated_market_value"])
        self.assertEqual(result["property_type"], "UNKNOWN")
        self.assertEqual(result["provenance"]["list_price"]["classification"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
