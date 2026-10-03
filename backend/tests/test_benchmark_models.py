import unittest
from datetime import datetime, timezone

from backend.app.benchmarks.models import (
    BenchmarkProperty,
    BenchmarkSignal,
    DataProvenance,
    TexasBenchmarkManifest,
)
from backend.app.providers.base import CanonicalProperty


class BenchmarkModelTests(unittest.TestCase):
    def property_record(self, county: str = "County A", state: str = "TX") -> BenchmarkProperty:
        canonical = CanonicalProperty(
            provider_property_id="provider-1",
            address="1 Main Street",
            city="Example City",
            state=state,
            zip_code="75001",
            property_type="single_family",
            list_price=250000,
            source="realtyapi",
            data_updated_at=datetime.now(timezone.utc),
        )
        return BenchmarkProperty(
            canonical=canonical,
            county=county,
            field_provenance={"list_price": DataProvenance.SOURCE},
        )

    def test_manifest_requires_two_distinct_counties(self):
        with self.assertRaises(ValueError):
            TexasBenchmarkManifest(state="TX", counties=["Dallas", "Dallas"])

    def test_manifest_accepts_two_counties_without_hard_coding_names(self):
        manifest = TexasBenchmarkManifest(
            state="tx",
            counties=["County A", "County B"],
            properties=[self.property_record("County A")],
        )
        self.assertEqual(manifest.state, "TX")
        self.assertEqual(manifest.properties_for_county("county a")[0].county, "County A")

    def test_property_requires_provenance_for_source_value(self):
        canonical = CanonicalProperty(
            provider_property_id="provider-2",
            address="2 Main Street",
            city="Example City",
            state="TX",
            zip_code="75001",
            property_type="single_family",
            list_price=300000,
            source="realtyapi",
            data_updated_at=datetime.now(timezone.utc),
        )
        with self.assertRaises(ValueError):
            BenchmarkProperty(canonical=canonical, county="County A")

    def test_positive_signal_cannot_be_unattributed(self):
        with self.assertRaises(ValueError):
            BenchmarkSignal(name="tax_delinquent", value=True, provenance=DataProvenance.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
