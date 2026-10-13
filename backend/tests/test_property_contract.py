import unittest

from backend.app.data.property_contract import canonical_property_response


class PropertyContractTests(unittest.TestCase):
    def test_persisted_row_uses_canonical_names_and_metadata(self):
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
            "photos": [],
            "provenance": {"list_price": {"classification": "UNKNOWN"}},
            "source_retrieved_at": "2026-10-04T00:00:00Z",
            "data_updated_at": None,
            "last_seen_at": "2026-10-04T00:00:00Z",
        })
        self.assertEqual(result["organization_property_id"], "org-property-1")
        self.assertEqual(result["provider_property_id"], "provider-1")
        self.assertEqual(result["zip_code"], "78744")
        self.assertNotIn("zip", result)
        self.assertIsNone(result["estimated_market_value"])
        self.assertEqual(result["property_type"], "UNKNOWN")
        self.assertEqual(result["provenance"]["list_price"]["classification"], "UNKNOWN")
        self.assertIsNone(result["data_updated_at"])

    def test_malformed_json_fields_are_returned_as_empty_collections(self):
        result = canonical_property_response({"id": "property-1", "photos": None, "provenance": []})
        self.assertEqual(result["photos"], [])
        self.assertEqual(result["provenance"], {})


if __name__ == "__main__":
    unittest.main()
