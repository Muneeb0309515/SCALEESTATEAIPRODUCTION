from typing import Literal
from datetime import datetime, timezone
import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from .core.config import get_settings
from .deal_engine import AnalysisInput, calculate_analysis
from .workflows import TransitionInput, validate_transition
from .matching import BuyerCriteria, DealCandidate, MatchConfiguration, match_buyer
from .services import IntegrationUnavailable, require_property_provider
from .comparables import ComparableCandidate, ComparableConfiguration, analyze_comparables
from .core.auth import AuthenticatedIdentity, require_authenticated_identity
from .data import OrganizationRepository, OrganizationScope, require_organization_scope
from .data.models import BuyerCreate, DealCreate, SavedSearchCreate, SellerCreate, TaskCreate
from .data.workflow_models import BuyerCriteriaUpdate, BuyerOfferCreate, ClosingRecord, DistributionCreate, DistributionResponse, FollowUpCreate, OutreachCreate, TransactionCreate
from .scoring import ClassificationConfiguration, WeightedScoreConfiguration, WeightedScoreInput, calculate_final_classification, calculate_weighted_score
from .motivation import MotivationInput, detect_motivation_signals
from .providers import get_property_provider
from .services.document_storage import get_document_url, put_document

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
    return {"status": "ready", "mode": "standalone_preview", "services": {"supabase_project": "disabled_by_request", "property_data": "disabled_by_request", "document_storage": "disabled_by_request", "ai_drafts": "disabled_by_request"}}

@app.get("/api/v1/auth/session")
async def auth_session(identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    return {"user_id": identity.user_id, "email": identity.email}

@app.get("/api/v1/properties")
async def list_properties(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("properties", "updated_at")

@app.get("/api/v1/search-us-market")
async def search_us_market(identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    """Approved discovery route: fails closed until an authorized provider adapter is active."""
    return await property_search_preview(identity)

@app.get("/api/v1/saved-searches")
async def list_saved_searches(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("saved_searches", "updated_at")

@app.post("/api/v1/saved-searches")
async def create_saved_search(payload: SavedSearchCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    record = repository.create("saved_searches", {**payload.model_dump(), "user_id": scope.user_id})
    repository.append_audit("saved_search", record["id"], "create", scope.user_id, new_value=record)
    return record

@app.get("/api/v1/properties/{property_id}")
async def get_property(property_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    record = OrganizationRepository(scope.organization_id).get("properties", property_id)
    if not record:
        raise HTTPException(status_code=404, detail={"code": "PROPERTY_NOT_FOUND", "message": "No property was found in this organization."})
    return record

@app.get("/api/v1/properties/{property_id}/sales-history")
async def get_sales_history(property_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("properties", property_id, "property")
    return repository.client.table("property_sales").select("*").eq("property_id", property_id).order("sale_date", desc=True).execute().data

@app.get("/api/v1/properties/{property_id}/listings-history")
async def get_listings_history(property_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("properties", property_id, "property")
    return repository.client.table("listing_history").select("*").eq("property_id", property_id).order("listing_date", desc=True).execute().data

@app.post("/api/v1/properties/{property_id}/motivation/analyze")
async def analyze_motivation(property_id: str, payload: MotivationInput, scope: OrganizationScope = Depends(require_organization_scope)):
    OrganizationRepository(scope.organization_id).require_record("properties", property_id, "property")
    return detect_motivation_signals(payload)

@app.get("/api/v1/properties/{property_id}/owner/contact-available")
async def contact_available(property_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("properties", property_id, "property")
    response = repository.client.table("owners").select("authorized_phone,authorized_email").eq("organization_id", scope.organization_id).eq("property_id", property_id).limit(1).execute()
    owner = response.data[0] if response.data else None
    return {"available": bool(owner and (owner.get("authorized_phone") or owner.get("authorized_email"))), "source": "owner authorized contact fields only"}

@app.get("/api/v1/deals")
async def list_deals(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("deals", "updated_at")

@app.post("/api/v1/deals")
async def create_deal(payload: DealCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("properties", payload.property_id, "property")
    if payload.seller_id:
        repository.require_record("sellers", payload.seller_id, "seller")
    record = repository.create("deals", payload.model_dump())
    repository.append_activity("deal_created", "Created a new deal", scope.user_id, record["id"])
    repository.append_audit("deal", record["id"], "create", scope.user_id, new_value=record)
    return record

@app.get("/api/v1/sellers")
async def list_sellers(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("sellers", "updated_at")

@app.post("/api/v1/sellers")
async def create_seller(payload: SellerCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    values = payload.model_dump(exclude={"contact_classification"})
    record = repository.create("sellers", values)
    repository.append_audit("seller", record["id"], "create", scope.user_id, new_value={**record, "contact_classification": payload.contact_classification})
    return record

@app.get("/api/v1/buyers")
async def list_buyers(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("buyers", "updated_at")

@app.post("/api/v1/buyers")
async def create_buyer(payload: BuyerCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    record = repository.create("buyers", payload.model_dump())
    repository.append_audit("buyer", record["id"], "create", scope.user_id, new_value=record)
    return record

@app.get("/api/v1/tasks")
async def list_tasks(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("tasks", "updated_at")

@app.post("/api/v1/tasks")
async def create_task(payload: TaskCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    record = repository.create("tasks", {**payload.model_dump(), "user_id": scope.user_id})
    repository.append_activity("task_created", "Created a deal task", scope.user_id, payload.deal_id)
    return record

@app.get("/api/v1/documents")
async def list_documents(scope: OrganizationScope = Depends(require_organization_scope)):
    return OrganizationRepository(scope.organization_id).list("documents")

@app.post("/api/v1/documents")
async def upload_document(
    document_type: str = Form(...),
    title: str = Form(...),
    deal_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    scope: OrganizationScope = Depends(require_organization_scope),
):
    repository = OrganizationRepository(scope.organization_id)
    if deal_id:
        repository.require_record("deals", deal_id, "deal")
    existing = repository.client.table("documents").select("version").eq("organization_id", scope.organization_id).eq("title", title).eq("document_type", document_type).order("version", desc=True).limit(1).execute().data
    version = (existing[0]["version"] if existing else 0) + 1
    storage_key, _ = await put_document(scope.organization_id, file)
    record = repository.create("documents", {"deal_id": deal_id, "document_type": document_type, "title": title, "storage_key": storage_key, "version": version, "uploaded_by": scope.user_id, "metadata": {"filename": file.filename, "content_type": file.content_type}})
    repository.append_audit("document", record["id"], "version_created", scope.user_id, new_value=record)
    repository.client.table("document_access_log").insert({"organization_id": scope.organization_id, "document_id": record["id"], "user_id": scope.user_id, "action": "uploaded"}).execute()
    return record

@app.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    document = repository.require_record("documents", document_id, "document")
    if document.get("deleted_at"):
        raise HTTPException(status_code=410, detail={"code": "DOCUMENT_SOFT_DELETED", "message": "The requested document version is no longer available."})
    url = await get_document_url(document["storage_key"])
    repository.client.table("document_access_log").insert({"organization_id": scope.organization_id, "document_id": document_id, "user_id": scope.user_id, "action": "downloaded"}).execute()
    return RedirectResponse(url=url, status_code=307)

@app.delete("/api/v1/documents/{document_id}")
async def soft_delete_document(document_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    document = repository.require_record("documents", document_id, "document")
    response = repository.client.table("documents").update({"deleted_at": datetime.now(timezone.utc).isoformat()}).eq("id", document_id).execute()
    repository.append_audit("document", document_id, "soft_delete", scope.user_id, old_value=document, new_value={"deleted_at": True})
    repository.client.table("document_access_log").insert({"organization_id": scope.organization_id, "document_id": document_id, "user_id": scope.user_id, "action": "access_denied"}).execute()
    return response.data[0]

@app.post("/api/v1/sellers/{seller_id}/outreach")
async def log_outreach(seller_id: str, payload: OutreachCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    if payload.send_requested:
        raise HTTPException(status_code=503, detail={"code": "MESSAGING_PROVIDER_REQUIRED", "message": "Email and SMS delivery require an approved configured provider; the outreach draft was not sent."})
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("sellers", seller_id, "seller")
    record = repository.create("outreach", {"seller_id": seller_id, "contact_method": payload.contact_method, "message": payload.message, "subject": payload.subject, "status": "logged"})
    repository.append_activity("outreach_logged", "Logged seller outreach", scope.user_id, details={"seller_id": seller_id, "outreach_id": record["id"]})
    return record

@app.get("/api/v1/sellers/{seller_id}/outreach-history")
async def outreach_history(seller_id: str, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("sellers", seller_id, "seller")
    return repository.client.table("outreach").select("*").eq("seller_id", seller_id).order("timestamp", desc=True).execute().data

@app.post("/api/v1/sellers/{seller_id}/follow-up")
async def create_follow_up(seller_id: str, payload: FollowUpCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("sellers", seller_id, "seller")
    record = repository.create("tasks", {"deal_id": payload.deal_id, "user_id": scope.user_id, "task_type": "seller_follow_up", "description": payload.notes, "due_date": payload.follow_up_date, "status": "pending"})
    repository.append_activity("seller_follow_up_created", "Created seller follow-up", scope.user_id, payload.deal_id, {"seller_id": seller_id, "task_id": record["id"]})
    return record

@app.put("/api/v1/buyers/{buyer_id}/criteria")
async def update_buyer_criteria(buyer_id: str, payload: BuyerCriteriaUpdate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("buyers", buyer_id, "buyer")
    response = repository.client.table("buyer_criteria").upsert({"buyer_id": buyer_id, **payload.model_dump()}).execute()
    repository.append_audit("buyer_criteria", buyer_id, "upsert", scope.user_id, new_value=payload.model_dump())
    return response.data[0]

@app.post("/api/v1/deals/{deal_id}/distribute")
async def prepare_distribution(deal_id: str, payload: DistributionCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("deals", deal_id, "deal")
    for buyer_id in payload.buyer_ids:
        repository.require_record("buyers", buyer_id, "buyer")
    records = [repository.create("buyer_distributions", {"deal_id": deal_id, "buyer_id": buyer_id, "response_status": "prepared", "buyer_response_text": payload.message}) for buyer_id in payload.buyer_ids]
    repository.append_activity("buyer_distribution_prepared", "Prepared buyer distribution; delivery requires a configured provider", scope.user_id, deal_id, {"buyer_count": len(records)})
    return {"status": "prepared_not_sent", "distributions": records}

@app.post("/api/v1/distributions/{distribution_id}/response")
async def record_distribution_response(distribution_id: str, payload: DistributionResponse, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    response = repository.client.table("buyer_distributions").update(payload.model_dump(exclude_none=True)).eq("id", distribution_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail={"code": "DISTRIBUTION_NOT_FOUND", "message": "No buyer distribution was found."})
    repository.append_audit("buyer_distribution", distribution_id, "response_recorded", scope.user_id, new_value=payload.model_dump(exclude_none=True))
    return response.data[0]

@app.post("/api/v1/deals/{deal_id}/buyer-offers")
async def record_buyer_offer(deal_id: str, buyer_id: str, payload: BuyerOfferCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("deals", deal_id, "deal")
    repository.require_record("buyers", buyer_id, "buyer")
    record = repository.create("buyer_offers", {"deal_id": deal_id, "buyer_id": buyer_id, **payload.model_dump(), "status": "received"})
    repository.append_activity("buyer_offer_received", "Recorded a buyer offer", scope.user_id, deal_id, {"buyer_id": buyer_id, "offer_id": record["id"]})
    return record

@app.post("/api/v1/transactions")
async def create_transaction(payload: TransactionCreate, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    repository.require_record("deals", payload.deal_id, "deal")
    repository.require_record("buyers", payload.buyer_id, "buyer")
    record = repository.create("transactions", {**payload.model_dump(), "status": "pending"})
    repository.append_audit("transaction", record["id"], "create", scope.user_id, new_value=record)
    return record

@app.post("/api/v1/transactions/{transaction_id}/close")
async def record_closing(transaction_id: str, payload: ClosingRecord, scope: OrganizationScope = Depends(require_organization_scope)):
    repository = OrganizationRepository(scope.organization_id)
    response = repository.client.table("transactions").update({"actual_closing_price": payload.closing_price, "closing_date": payload.closing_date, "closing_costs": payload.closing_costs, "final_net": payload.final_net, "status": "closed"}).eq("id", transaction_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail={"code": "TRANSACTION_NOT_FOUND", "message": "No transaction was found."})
    repository.append_audit("transaction", transaction_id, "closing_recorded", scope.user_id, new_value=payload.model_dump())
    return response.data[0]

@app.post("/api/v1/deal-analysis")
async def deal_analysis(payload: AnalysisInput, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    return calculate_analysis(payload)

@app.post("/api/v1/deals/validate-transition")
async def validate_deal_transition(payload: TransitionInput, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    """Return only documented stage-transition actions for the persistence layer."""
    result = validate_transition(payload)
    if not result.allowed:
        raise HTTPException(status_code=result.status_code, detail={"code": "INVALID_STAGE_TRANSITION", "message": result.reason})
    return result

@app.post("/api/v1/matching/preview")
async def preview_buyer_match(deal: DealCandidate, buyer: BuyerCriteria, configuration: MatchConfiguration, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    """Calculate an explainable buyer match; stored results belong to the persistence layer."""
    return match_buyer(deal, buyer, configuration)

@app.get("/api/v1/providers/property-search")
async def property_search_preview(identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    """Integration gate; a provider adapter is never substituted with mock records."""
    try:
        require_property_provider()
    except IntegrationUnavailable as error:
        raise HTTPException(status_code=503, detail={"code": error.code, "message": error.message}) from error
    return get_property_provider()

@app.post("/api/v1/comparables/analyze")
async def analyze_comparable_sales(candidates: list[ComparableCandidate], configuration: ComparableConfiguration, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    """Return an explainable deterministic comp review; database persistence is separate."""
    return analyze_comparables(candidates, configuration)

@app.post("/api/v1/scoring/weighted")
async def calculate_score(score_input: WeightedScoreInput, configuration: WeightedScoreConfiguration, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    return {"score": calculate_weighted_score(score_input, configuration), "classification": "CALCULATED_DATA", "formula": "Score = Σ(Factor Score × Configured Weight)"}

@app.post("/api/v1/scoring/classification")
async def calculate_classification(deal_score: float | None, risk_score: float | None, configuration: ClassificationConfiguration | None, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    return calculate_final_classification(deal_score, risk_score, configuration)

@app.post("/api/v1/ai/drafts")
async def create_reviewable_draft(payload: DraftRequest, identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
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
async def document_upload_intent(identity: AuthenticatedIdentity = Depends(require_authenticated_identity)):
    if not get_settings().has_project_supabase_connection:
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Secure document storage requires authenticated organization access and a restricted S3 document bucket."})
    raise HTTPException(status_code=501, detail={"code": "AUTHORIZATION_REQUIRED", "message": "Signed organization-authorized upload flow is disabled in the standalone preview."})
