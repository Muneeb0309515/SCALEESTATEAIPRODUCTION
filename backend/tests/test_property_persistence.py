import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
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
        self.upserted = None

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

    def upsert(self, values, on_conflict=None):
        self.upserted = values
        return self

    def execute(self):
        table = self.store.setdefault(self.table_name, [])
        rows = list(table)
        for field, value in self.filters:
            rows = [row for row in rows if row.get(field) == value]
        if self.inserted is not None:
            record = {"id": f"{self.table_name}-{len(table) + 1}", **self.inserted}
            table.append(record)
            return SimpleNamespace(data=[record])
        if self.upserted is not None:
            written = []
            for values in self.upserted:
                existing = next((row for row in table if row.get("property_id") == values.get("property_id") and row.get("field_name") == values.get("field_name")), None)
                if existing:
                    existing.update(values)
                    written.append(existing)
                else:
                    record = {"id": f"{self.table_name}-{len(table) + 1}", **values}
                    table.append(record)
                    written.append(record)
            return SimpleNamespace(data=written)
        if self.updated is not None:
            for row in rows:
                row.update(self.updated)
            return SimpleNamespace(data=rows[:1])
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, table_name):
        return FakeQuery(table_name, self.store)


class FakeUniqueViolation(Exception):
    code = "23505"


class ConcurrentStore(dict):
    def __init__(self, party_count):
        super().__init__({"properties": [], "property_fields": []})
        self.lock = threading.RLock()
        self.initial_lookup_count = 0
        self.initial_lookup_barrier = threading.Barrier(party_count)


class ConcurrentQuery(FakeQuery):
    def execute(self):
        is_property_lookup = (
            self.table_name == "properties"
            and self.inserted is None
            and self.updated is None
            and self.upserted is None
        )
        wait_for_initial_lookup = False
        if is_property_lookup:
            with self.store.lock:
                if self.store.initial_lookup_count < self.store.initial_lookup_barrier.parties:
                    self.store.initial_lookup_count += 1
                    wait_for_initial_lookup = True
            snapshot = super().execute()
            if wait_for_initial_lookup:
                self.store.initial_lookup_barrier.wait(timeout=10)
            return snapshot

        with self.store.lock:
            if self.table_name == "properties" and self.inserted is not None:
                table = self.store.setdefault("properties", [])
                duplicate = any(
                    row.get("organization_id") == self.inserted.get("organization_id")
                    and row.get("source") == self.inserted.get("source")
                    and row.get("provider_property_id") == self.inserted.get("provider_property_id")
                    and row.get("provider_property_id") is not None
                    for row in table
                )
                if duplicate:
                    raise FakeUniqueViolation("duplicate key violates properties organization/source/provider unique index")
            return super().execute()


class ConcurrentFakeClient(FakeClient):
    def table(self, table_name):
        return ConcurrentQuery(table_name, self.store)


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
            "lot_size": 4200,
            "photos": ["https://example.test/house.jpg"],
            "source": "realtyapi",
            "data_updated_at": datetime(2026, 9, 15, tzinfo=timezone.utc),
        }
        values.update(changes)
        return CanonicalProperty(**values)

    def test_upsert_persists_provider_identity_and_field_provenance(self):
        store = {"properties": [], "property_fields": []}
        record = self.repository(store).upsert_property(self.property_record())
        self.assertEqual(record["organization_id"], "org-a")
        self.assertEqual(record["source"], "realtyapi")
        self.assertEqual(record["provider_property_id"], "realty-property-1")
        self.assertEqual(record["provider_listing_id"], "realty-listing-1")
        self.assertEqual(record["provenance"]["list_price"]["classification"], "SOURCE_DATA")
        self.assertEqual(record["provenance"]["latitude"]["classification"], "UNKNOWN")
        self.assertEqual(len(store["property_fields"]), 21)
        lot_field = next(field for field in store["property_fields"] if field["field_name"] == "lot_size")
        self.assertEqual(lot_field["classification"], "SOURCE_DATA")
        self.assertEqual(lot_field["source"], "realtyapi")

    def test_sparse_provider_response_does_not_erase_known_values_or_provenance(self):
        store = {"properties": [], "property_fields": []}
        repository = self.repository(store)
        first = repository.upsert_property(self.property_record())
        second = repository.upsert_property(self.property_record(living_area=None, lot_size=None, list_price=280000, data_updated_at=None))
        self.assertEqual(first["id"], second["id"])
        persisted = store["properties"][0]
        self.assertEqual(persisted["living_area"], 1500)
        self.assertEqual(persisted["lot_size"], 4200)
        self.assertEqual(persisted["list_price"], 280000)
        self.assertEqual(persisted["data_updated_at"], "2026-09-15T00:00:00+00:00")
        self.assertEqual(persisted["provenance"]["living_area"]["classification"], "SOURCE_DATA")
        living_field = next(field for field in store["property_fields"] if field["field_name"] == "living_area")
        self.assertEqual(living_field["value"], 1500)
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

    def test_concurrent_same_listing_recovers_unique_conflicts_without_503_errors_or_duplicates(self):
        request_count = 8
        store = ConcurrentStore(request_count)
        repositories = [self.repository(store) for _ in range(request_count)]
        for repository in repositories:
            repository.client = ConcurrentFakeClient(store)

        with ThreadPoolExecutor(max_workers=request_count) as executor:
            records = list(
                executor.map(
                    lambda repository: repository.upsert_property(self.property_record()),
                    repositories,
                )
            )

        self.assertEqual(len(records), request_count)
        self.assertEqual(len(store["properties"]), 1)
        self.assertEqual(len({record["id"] for record in records}), 1)
        self.assertEqual(len(store["property_fields"]), 21)


if __name__ == "__main__":
    unittest.main()
