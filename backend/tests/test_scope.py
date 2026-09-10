import unittest
from fastapi import HTTPException
from backend.app.data.scope import require_organization_scope
from backend.app.core.auth import AuthenticatedIdentity


class ScopeTests(unittest.TestCase):
    def test_scope_requires_membership_when_called_after_authentication(self):
        identity = AuthenticatedIdentity(user_id="test", email=None)
        with self.assertRaises(HTTPException) as error:
            require_organization_scope(identity, None)
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail["code"], "ORGANIZATION_REQUIRED")

if __name__ == "__main__": unittest.main()
