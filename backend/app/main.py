from typing import Literal
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .core.config import get_settings
from .deal_engine import AnalysisInput, calculate_analysis
from .workflows import TransitionInput, validate_transition
from .matching import BuyerCriteria, DealCandidate, MatchConfiguration, match_buyer

app = FastAPI(title="SCALEESTATE AI API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

class VerifiedFact(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=1000)
    source: str = Field(min_length=1, max_length=200)
    confidence: Literal["VERIFIED"]

class DraftRequest(BaseModel):
    draft_type: Literal["seller_outreach", "research_summary"]
    verified_facts: list[VerifiedFact] = Field(min_length=1, max_length=60)
    user_instruction: str = Field(default="", max_length=1500)

@app.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ready", "services": {"supabase_project": "configured" if settings.has_project_supabase_connection else "configuration_required", "ai_drafts": "configured" if settings.has_llm_connection else "configuration_required"}}

@app.post("/api/v1/deal-analysis")
async def deal_analysis(payload: AnalysisInput):
    return calculate_analysis(payload)

@app.post("/api/v1/deals/validate-transition")
async def validate_deal_transition(payload: TransitionInput):
    """Return only documented stage-transition actions for the persistence layer."""
    result = validate_transition(payload)
    if not result.allowed:
        raise HTTPException(status_code=result.status_code, detail={"code": "INVALID_STAGE_TRANSITION", "message": result.reason})
    return result

@app.post("/api/v1/matching/preview")
async def preview_buyer_match(deal: DealCandidate, buyer: BuyerCriteria, configuration: MatchConfiguration):
    """Calculate an explainable buyer match; stored results belong to the persistence layer."""
    return match_buyer(deal, buyer, configuration)

@app.post("/api/v1/ai/drafts")
async def create_reviewable_draft(payload: DraftRequest):
    settings = get_settings()
    if not settings.has_llm_connection:
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "AI drafting is unavailable until the server-only LLM connection is configured."})
    facts = "\n".join(f"- {fact.field}: {fact.value} (source: {fact.source}; confidence: VERIFIED)" for fact in payload.verified_facts)
    system = "Draft real-estate seller outreach or research summaries. Use ONLY verified facts supplied. Never add facts, contacts, financial values, promises, or claims of seller motivation. Do not calculate financial metrics. Return only a user-reviewable draft."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{settings.built_in_forge_api_url.rstrip('/')}/v1/chat/completions", headers={"Authorization": f"Bearer {settings.built_in_forge_api_key}"}, json={"model": "gpt-5-mini", "messages": [{"role": "system", "content": system}, {"role": "user", "content": f"Draft type: {payload.draft_type}\nVerified facts:\n{facts}\nUser instruction: {payload.user_instruction}"}], "max_completion_tokens": 700})
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError) as error:
        raise HTTPException(status_code=502, detail={"code": "AI_DRAFT_UNAVAILABLE", "message": "The AI provider did not return a reviewable draft."}) from error
    return {"label": "AI-generated draft — user review required", "allowed_context": "verified property and owner facts only", "content": content}

@app.post("/api/v1/documents/upload-intent")
async def document_upload_intent():
    if not get_settings().has_project_supabase_connection:
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Secure document storage requires a direct Supabase project connection and restricted storage bucket."})
    raise HTTPException(status_code=501, detail={"code": "AUTHORIZATION_REQUIRED", "message": "Signed organization-authorized upload flow awaits validated Supabase Auth."})
