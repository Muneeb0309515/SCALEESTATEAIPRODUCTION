import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException
from backend.app.data.repository import OrganizationRepository


class RepositoryContractTests(unittest.TestCase):
    def test_missing_record_is_a_scoped_not_found_error(self):
        repository = object.__new__(OrganizationRepository)
        repository.get = MagicMock(return_value=None)
        with self.assertRaises(HTTPException) as error:
            repository.require_record("deals", "other-org-record", "deal")
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(error.exception.detail["code"], "DEAL_NOT_FOUND")

if __name__ == "__main__": unittest.main()
