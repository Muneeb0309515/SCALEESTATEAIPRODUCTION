import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
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

    def test_valid_es256_supabase_token_is_accepted(self):
        private_key = ec.generate_private_key(ec.SECP256R1())
        token = jwt.encode(self._claims(), private_key, algorithm="ES256")
        public_key = private_key.public_key()
        settings = SimpleNamespace(has_project_supabase_connection=True, supabase_project_url="https://project.supabase.co", supabase_key="service-key")
        signing_key = SimpleNamespace(key=public_key)
        with patch("backend.app.core.auth.get_settings", return_value=settings), patch("backend.app.core.auth._jwks_client") as jwks:
            jwks.return_value.get_signing_key_from_jwt.return_value = signing_key
            identity = require_authenticated_identity(f"Bearer {token}")
        self.assertEqual(identity.user_id, "user-123")
        self.assertEqual(identity.email, "owner@example.com")

    def test_invalid_es256_claims_and_signature_are_rejected(self):
        private_key = ec.generate_private_key(ec.SECP256R1())
        other_key = ec.generate_private_key(ec.SECP256R1())
        settings = SimpleNamespace(has_project_supabase_connection=True, supabase_project_url="https://project.supabase.co", supabase_key="service-key")
        signing_key = SimpleNamespace(key=private_key.public_key())
        cases = {
            "issuer": {"iss": "https://wrong.supabase.co/auth/v1"},
            "audience": {"aud": "public"},
            "expired": {"exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        }
        for label, overrides in cases.items():
            with self.subTest(label=label):
                claims = self._claims()
                claims.update(overrides)
                token = jwt.encode(claims, private_key, algorithm="ES256")
                with patch("backend.app.core.auth.get_settings", return_value=settings), patch("backend.app.core.auth._jwks_client") as jwks:
                    jwks.return_value.get_signing_key_from_jwt.return_value = signing_key
                    with self.assertRaises(HTTPException) as error:
                        require_authenticated_identity(f"Bearer {token}")
                self.assertEqual(error.exception.status_code, 401)
                self.assertEqual(error.exception.detail["code"], "INVALID_SESSION")

        with self.subTest(label="signature"):
            token = jwt.encode(self._claims(), other_key, algorithm="ES256")
            with patch("backend.app.core.auth.get_settings", return_value=settings), patch("backend.app.core.auth._jwks_client") as jwks:
                jwks.return_value.get_signing_key_from_jwt.return_value = signing_key
                with self.assertRaises(HTTPException) as error:
                    require_authenticated_identity(f"Bearer {token}")
            self.assertEqual(error.exception.status_code, 401)
            self.assertEqual(error.exception.detail["code"], "INVALID_SESSION")

    @staticmethod
    def _claims():
        now = datetime.now(timezone.utc)
        return {
            "sub": "user-123",
            "email": "owner@example.com",
            "aud": "authenticated",
            "iss": "https://project.supabase.co/auth/v1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }


if __name__ == "__main__":
    unittest.main()
