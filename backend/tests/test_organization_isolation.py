import unittest
from types import SimpleNamespace

from backend.app.data.repository import OrganizationRepository


class FakeQuery:
    def __init__(self, table_name, store):
        self.table_name = table_name
        self.store = store
        self.filters = []
        self.inserted = None

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

    def execute(self):
        if self.inserted is not None:
            record = {"id": "created", **self.inserted}
            self.store.setdefault(self.table_name, []).append(record)
            return SimpleNamespace(data=[record])
        rows = list(self.store.get(self.table_name, []))
        for field, value in self.filters:
            rows = [row for row in rows if row.get(field) == value]
        return SimpleNamespace(data=rows)


class FakeClient:
    def __init__(self, store):
        self.store = store
        self.queries = []

    def table(self, table_name):
        query = FakeQuery(table_name, self.store)
        self.queries.append(query)
        return query


class OrganizationIsolationTests(unittest.TestCase):
    def repository(self, organization_id="org-a"):
        repository = object.__new__(OrganizationRepository)
        repository.organization_id = organization_id
        repository.client = FakeClient({
            "properties": [
                {"id": "property-a", "organization_id": "org-a"},
                {"id": "property-b", "organization_id": "org-b"},
            ],
            "deals": [
                {"id": "deal-a", "organization_id": "org-a"},
                {"id": "deal-b", "organization_id": "org-b"},
            ],
            "buyers": [
                {"id": "buyer-a", "organization_id": "org-a"},
                {"id": "buyer-b", "organization_id": "org-b"},
            ],
            "documents": [
                {"id": "document-a", "organization_id": "org-a"},
                {"id": "document-b", "organization_id": "org-b"},
            ],
        })
        return repository

    def test_same_organization_is_allowed_for_critical_resources(self):
        repository = self.repository("org-a")
        for table, record_id in (
            ("properties", "property-a"),
            ("deals", "deal-a"),
            ("buyers", "buyer-a"),
            ("documents", "document-a"),
        ):
            with self.subTest(table=table):
                record = repository.require_record(table, record_id, table[:-1])
                self.assertEqual(record["organization_id"], "org-a")

    def test_different_organization_is_denied_for_critical_resources(self):
        repository = self.repository("org-a")
        for table, record_id, label in (
            ("properties", "property-b", "property"),
            ("deals", "deal-b", "deal"),
            ("buyers", "buyer-b", "buyer"),
            ("documents", "document-b", "document"),
        ):
            with self.subTest(table=table):
                with self.assertRaises(Exception) as error:
                    repository.require_record(table, record_id, label)
                self.assertEqual(error.exception.status_code, 404)
                self.assertEqual(error.exception.detail["code"], f"{label.upper()}_NOT_FOUND")

    def test_writes_cannot_override_repository_organization(self):
        repository = self.repository("org-a")
        record = repository.create("deals", {"organization_id": "org-b", "notes": "test"})
        self.assertEqual(record["organization_id"], "org-a")


if __name__ == "__main__":
    unittest.main()
