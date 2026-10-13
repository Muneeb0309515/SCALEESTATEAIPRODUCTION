import unittest

from backend.app.data.property_contract import canonical_property_response
from backend.app.providers.photo_urls import sanitize_provider_photo_url, sanitize_provider_photo_urls


class PropertyPhotoUrlPolicyTests(unittest.TestCase):
    def test_trusted_provider_domains_accept_secure_photo_urls(self):
        self.assertEqual(
            sanitize_provider_photo_url("https://ap.rdcpix.com/photo.jpg?size=large"),
            "https://ap.rdcpix.com/photo.jpg?size=large",
        )
        self.assertEqual(
            sanitize_provider_photo_url("https://photos.realtyapi.io/photo.jpg"),
            "https://photos.realtyapi.io/photo.jpg",
        )
        self.assertEqual(
            sanitize_provider_photo_url("https://photos.realtor.com/photo.jpg"),
            "https://photos.realtor.com/photo.jpg",
        )

    def test_untrusted_schemes_hosts_credentials_and_ports_are_rejected(self):
        for url in (
            "javascript:alert(1)",
            "data:image/svg+xml,<svg/>",
            "http://ap.rdcpix.com/photo.jpg",
            "https:///ap.rdcpix.com/photo.jpg",
            "https:ap.rdcpix.com/photo.jpg",
            "https://rdcpix.com.attacker.example/photo.jpg",
            "https://ap.rdcpix.com@attacker.example/photo.jpg",
            "https://@ap.rdcpix.com/photo.jpg",
            "https://user@ap.rdcpix.com/photo.jpg",
            "https://ap.rdcpix.com:/photo.jpg",
            "https://ap.rdcpix.com:444/photo.jpg",
            "//ap.rdcpix.com/photo.jpg",
            " https://ap.rdcpix.com/photo.jpg",
            "https://ap.rdcpix.com\\@attacker.example/photo.jpg",
        ):
            with self.subTest(url=url):
                self.assertIsNone(sanitize_provider_photo_url(url))

    def test_photo_list_is_filtered_and_deduplicated(self):
        self.assertEqual(
            sanitize_provider_photo_urls([
                "https://ap.rdcpix.com/one.jpg",
                "https://attacker.example/evil.jpg",
                "https://ap.rdcpix.com/one.jpg",
                None,
            ]),
            ["https://ap.rdcpix.com/one.jpg"],
        )

    def test_legacy_unsafe_database_photo_urls_are_removed_from_api_contract(self):
        response = canonical_property_response({
            "id": "property-1",
            "primary_photo": "javascript:alert(1)",
            "photos": ["https://attacker.example/stored.jpg", "https://ap.rdcpix.com/good.jpg"],
        })
        self.assertIsNone(response["primary_photo"])
        self.assertEqual(response["photos"], ["https://ap.rdcpix.com/good.jpg"])


if __name__ == "__main__":
    unittest.main()
