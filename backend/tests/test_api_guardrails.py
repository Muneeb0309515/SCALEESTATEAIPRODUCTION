import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import app
from backend.app.main import DraftRequest


class ApiGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ai_draft_model_rejects_non_verified_context(self):
        with self.assertRaises(ValidationError):
            DraftRequest(draft_type="seller_outreach", verified_facts=[{"field": "Owner", "value": "Example", "source": "unverified source", "confidence": "UNVERIFIED"}])

    def test_document_upload_does_not_succeed_without_authorized_storage_flow(self):
        response = self.client.post("/api/v1/documents/upload-intent")
        self.assertEqual(response.status_code, 503)

    def test_deterministic_api_requires_authenticated_identity(self):
        response = self.client.post("/api/v1/deal-analysis", json={"arv": {"classification": "AI_ESTIMATE", "value": 300000, "source": "draft"}})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "CONFIGURATION_REQUIRED")

if __name__ == "__main__": unittest.main()
