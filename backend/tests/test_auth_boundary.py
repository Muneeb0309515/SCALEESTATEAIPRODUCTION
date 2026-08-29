import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.core.auth import require_authenticated_identity


class AuthenticationBoundaryTests(unittest.TestCase):
    def test_authentication_fails_closed_without_a_validated_project_connection(self):
        with patch("backend.app.core.auth.get_settings", return_value=SimpleNamespace(has_project_supabase_connection=False)):
            with self.assertRaises(HTTPException) as error:
                require_authenticated_identity(None)
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail["code"], "CONFIGURATION_REQUIRED")

    def test_validated_project_requires_a_bearer_token(self):
        with patch("backend.app.core.auth.get_settings", return_value=SimpleNamespace(has_project_supabase_connection=True)):
            with self.assertRaises(HTTPException) as error:
                require_authenticated_identity(None)
        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(error.exception.detail["code"], "AUTHENTICATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
