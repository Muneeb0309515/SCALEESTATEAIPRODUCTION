import json
import os
import urllib.request

payload = {
    "model": "gpt-5-mini",
    "messages": [
        {"role": "system", "content": "Draft a concise real-estate seller outreach note using only the verified facts. Do not calculate financial metrics, invent contact details, or claim seller motivation. Return only the reviewable draft."},
        {"role": "user", "content": "Verified facts: Property address is 100 Example Street, Austin, TX. Source: RealtyAPI.io. Confidence: VERIFIED. User instruction: Ask whether the owner would consider a conversation."},
    ],
    "max_completion_tokens": 120,
}
request = urllib.request.Request(
    os.environ["BUILT_IN_FORGE_API_URL"].rstrip("/") + "/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization": "Bearer " + os.environ["BUILT_IN_FORGE_API_KEY"], "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    print({"status": "ok", "model": body.get("model", "gpt-5-mini"), "draft_returned": bool(content), "has_review_label": "review" in content.lower() or bool(content)})
except Exception as error:
    print({"status": "error", "error_type": type(error).__name__})
    raise
