import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from backend.app.data.repository import OrganizationRepository
from backend.app.providers.base import CanonicalProperty


class FakeQuery:
    def __init__(self, table_name, store):
        self.table_name = table_name
        self.store = store
        self.filters = []
        self.inserted = None
        self.updated = None

    def select(self, *_columns):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def insert(self, values):
        self.inserted = values
        return self

    def update(self, values):
        self.updated = values
        return self

    def execute(self):
        rows = list(self.store.setdefault(self.table_name, []))
        for field, value in self.filters:
            rows = [row for row in rows if row.get(field) == value]
        if self.inserted is not None:
            record = {"id": f"{self.table_name}-{len(self.store[self.table_name]) + 1}", **self.inserted}
            self.store[self.table_name].append(record)
            return SimpleNamespace(data=[record])
        if self.updated is not None:
            for row in self.store[self.table_name]:
                if row in rows:
                    row.update(self.updated)
            return SimpleNamespace(data=rows[:1])
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, table_name):
        return FakeQuery(table_name, self.store)


class PropertyPersistenceTests(unittest.TestCase):
    def repository(self, store, organization_id="org-a"):
        repository = object.__new__(OrganizationRepository)
        repository.organization_id = organization_id
        repository.client = FakeClient(store)
        return repository

    @staticmethod
    def property_record(**changes):
        values = {
            "provider_property_id": "realty-property-1",
            "provider_listing_id": "realty-listing-1",
            "address": "123 Main St, Austin, TX 78744",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78744",
            "property_type": "single_family",
            "list_price": 275000,
            "beds": 3,
            "baths": 2.0,
            "living_area": 1500,
            "source": "realtyapi",
            "data_updated_at": datetime(2026, 9, 15, tzinfo=timezone.utc),
        }
        values.update(changes)
        return CanonicalProperty(**values)

    def test_upsert_persists_source_identity_and_field_provenance(self):
        store = {"properties": [], "property_fields": []}
        record = self.repository(store).upsert_property(self.property_record(lot_size=None))

        self.assertEqual(record["organization_id"], "org-a")
        self.assertEqual(record["source"], "realtyapi")
        self.assertEqual(record["provider_property_id"], "realty-property-1")
        self.assertEqual(record["provenance"]["list_price"]["classification"], "SOURCE_DATA")
        self.assertEqual(record["provenance"]["lot_size"]["classification"], "UNKNOWN")
        self.assertEqual(len(store["property_fields"]), 21)
        lot_field = next(field for field in store["property_fields"] if field["field_name"] == "lot_size")
        self.assertEqual(lot_field["classification"], "UNKNOWN")
        self.assertIsNone(lot_field["source"])

    def test_sparse_provider_response_does_not_erase_prior_known_value(self):
        store = {"properties": [], "property_fields": []}
        repository = self.repository(store)
        first = repository.upsert_property(self.property_record(living_area=1500))
        second = repository.upsert_property(self.property_record(living_area=None, list_price=280000))

        self.assertEqual(first["id"], second["id"])
        persisted = store["properties"][0]
        self.assertEqual(persisted["living_area"], 1500)
        self.assertEqual(persisted["list_price"], 280000)
        self.assertEqual(len(store["properties"]), 1)

    def test_provider_identity_is_scoped_to_organization(self):
        store = {
            "properties": [{"id": "org-b-property", "organization_id": "org-b", "source": "realtyapi", "provider_property_id": "realty-property-1"}],
            "property_fields": [],
        }
        record = self.repository(store, "org-a").upsert_property(self.property_record())

        self.assertEqual(record["organization_id"], "org-a")
        self.assertEqual(len(store["properties"]), 2)
        self.assertNotEqual(record["id"], "org-b-property")


if __name__ == "__main__":
    unittest.main()
