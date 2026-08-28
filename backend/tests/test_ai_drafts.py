import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import main


class FakeAiResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "Hello, would you be open to a conversation about the property?"}}]}


class FakeAiClient:
    last_request = None

    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, **kwargs):
        FakeAiClient.last_request = (url, kwargs)
        return FakeAiResponse()


class AiDraftTests(unittest.TestCase):
    def test_verified_facts_call_returns_reviewable_draft(self):
        identity = SimpleNamespace(user_id="user-1", email="owner@example.com")
        settings = SimpleNamespace(
            has_llm_connection=True,
            built_in_forge_api_url="https://forge.example",
            built_in_forge_api_key="server-key",
        )
        main.app.dependency_overrides[main.require_authenticated_identity] = lambda: identity
        try:
            with patch.object(main, "get_settings", return_value=settings), patch.object(main.httpx, "AsyncClient", FakeAiClient):
                response = TestClient(main.app).post(
                    "/api/v1/ai/drafts",
                    json={
                        "draft_type": "seller_outreach",
                        "verified_facts": [{"field": "Property address", "value": "123 Main St, Austin, TX", "source": "realtyapi", "confidence": "VERIFIED"}],
                        "user_instruction": "Ask for a conversation.",
                    },
                )
        finally:
            main.app.dependency_overrides.pop(main.require_authenticated_identity, None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["label"], "AI-generated draft — user review required")
        self.assertIn("verified property and owner facts only", response.json()["allowed_context"])
        self.assertEqual(FakeAiClient.last_request[1]["json"]["model"], "gpt-5-mini")
        self.assertIn("confidence: VERIFIED", FakeAiClient.last_request[1]["json"]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
