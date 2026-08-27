import unittest
from fastapi import HTTPException
from backend.app.core.auth import require_authenticated_identity


class AuthenticationBoundaryTests(unittest.TestCase):
    def test_authentication_fails_closed_without_a_validated_project_connection(self):
        with self.assertRaises(HTTPException) as error:
            require_authenticated_identity(None)
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail["code"], "CONFIGURATION_REQUIRED")

if __name__ == "__main__": unittest.main()
