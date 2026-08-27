import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class ApiGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ai_draft_rejects_non_verified_context_before_provider_call(self):
        response = self.client.post("/api/v1/ai/drafts", json={"draft_type": "seller_outreach", "verified_facts": [{"field": "Owner", "value": "Example", "source": "unverified source", "confidence": "UNVERIFIED"}]})
        self.assertEqual(response.status_code, 422)

    def test_document_upload_does_not_succeed_without_authorized_storage_flow(self):
        response = self.client.post("/api/v1/documents/upload-intent")
        self.assertIn(response.status_code, (501, 503))

    def test_ai_estimated_arv_is_not_returned_as_a_calculation_input(self):
        response = self.client.post("/api/v1/deal-analysis", json={"arv": {"classification": "AI_ESTIMATE", "value": 300000, "source": "draft"}})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["arv"]["state"], "INSUFFICIENT_DATA")
        self.assertIsNone(payload["arv"]["value"])

if __name__ == "__main__": unittest.main()
