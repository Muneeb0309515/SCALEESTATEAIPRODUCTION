SCALEESTATE AI — DETERMINISTIC DEAL ANALYSIS ENGINE

Version

1.0

Status

AUTHORITATIVE / SOURCE OF TRUTH

Purpose

This document defines the deterministic financial and investment-analysis rules used by SCALEESTATE AI.

The system MUST use deterministic backend logic for financial calculations.

The LLM/AI agent MUST NOT independently invent, modify, or recalculate financial formulas defined in this document.

The purpose of this engine is to transform verified, normalized property and market data into transparent, reproducible investment-analysis results.

---

1. CORE PRINCIPLES

1.1 Deterministic Calculations

Every financial metric defined in this document MUST be calculated by backend code.

The same input data and configuration MUST produce the same output.

The LLM may explain results but MUST NOT replace the calculation engine.

---

1.2 No Fabricated Data

The engine MUST NOT create:

- Fake property values
- Fake comparable sales
- Fake owner information
- Fake sale prices
- Fake repair costs
- Fake market data
- Fake equity
- Fake ARV
- Fake financial projections

If required data is unavailable, return:

"UNKNOWN"

or an appropriate confidence/error state.

---

1.3 Data Provenance

Every important value should retain its origin.

Possible classifications:

- "SOURCE_DATA"
- "NORMALIZED_DATA"
- "CALCULATED_DATA"
- "AI_ESTIMATE"
- "USER_INPUT"
- "UNKNOWN"

The system MUST NOT present an AI estimate as verified source data.

---

2. DATA CLASSIFICATION

SOURCE_DATA

Information directly retrieved from an external data provider or authoritative source.

Examples:

- Listing price
- Sale price
- Sale date
- Property address
- Beds
- Baths
- Square footage
- Year built
- Property type
- Owner record

---

NORMALIZED_DATA

Source data transformed into a standardized format.

Examples:

- Standardized address
- Normalized property type
- Standardized square footage
- Parsed dates
- Standardized monetary values

---

CALCULATED_DATA

Values mathematically derived from available data.

Examples:

- Price per square foot
- Weighted comparable value
- ARV
- Equity
- MAO
- Wholesale spread
- ROI
- Deal score

---

AI_ESTIMATE

Values estimated through an AI/model-based process rather than deterministic verified data.

Examples:

- Qualitative condition estimate
- AI-generated repair estimate
- Motivated-seller interpretation

AI estimates MUST be clearly labeled.

---

USER_INPUT

Information explicitly entered or approved by the user.

Examples:

- Expected repair budget
- Desired wholesale fee
- Custom MAO percentage
- Investment strategy
- Target market

---

UNKNOWN

Information that cannot currently be verified or calculated.

---

3. PROPERTY DATA REQUIREMENTS

For each property, collect where available:

- Address
- City
- State
- ZIP
- Property type
- Beds
- Baths
- Living area
- Lot size
- Year built
- Current asking price
- Last sale price
- Last sale date
- Property tax
- Ownership information
- Listing status
- Property condition
- Market information

Missing data MUST NOT be silently replaced with assumptions.

---

4. COMPARABLE PROPERTY ENGINE

4.1 Purpose

The Comparable Engine identifies recently sold properties that can reasonably represent the subject property's market value.

Comparable selection MUST be systematic and reproducible.

---

4.2 Primary Comparable Criteria

Prioritize:

1. Same property type
2. Geographic proximity
3. Recent sale date
4. Similar living area
5. Similar bedroom count
6. Similar bathroom count
7. Similar year built
8. Similar lot characteristics where available

---

5. DISTANCE TIERS

Use configurable geographic tiers.

Recommended default:

Tier 1

Within "0.5 miles"

Tier 2

Within "1.0 mile"

Tier 3

Within "2.0 miles"

Tier 4

Beyond "2.0 miles"

Tier 1 comparables receive the strongest geographic preference.

The engine may expand the search radius when insufficient qualified comparables exist.

The expansion MUST be recorded.

---

6. SALE RECENCY

Prioritize the newest transactions.

Default preference:

- 0–3 months: Excellent
- 3–6 months: Strong
- 6–12 months: Acceptable
- 12–18 months: Weak
- «18 months: Poor unless market conditions justify inclusion»

The system MUST record sale dates.

---

7. SIZE SIMILARITY

Compare subject living area against comparable living area.

Default target:

"±20%"

Preferred:

"±10%"

A comparable outside the preferred range may still be used when insufficient qualified comps exist.

---

8. BEDROOM AND BATHROOM SIMILARITY

Prefer exact or near-exact matches.

Scoring preference:

- Exact match = highest
- Difference of 1 = acceptable
- Difference greater than 1 = weak

Bathrooms may use fractional values when the source supports them.

---

9. YEAR BUILT

Prefer properties with similar construction age.

The engine should prioritize:

"±10 years"

when sufficient data exists.

Year-built similarity should influence comparable quality but should not automatically exclude otherwise highly relevant properties.

---

10. PRICE PER SQUARE FOOT

For each comparable:

"Price Per Sq Ft = Sale Price / Living Area"

This value MUST be calculated by backend code.

Do not allow the LLM to calculate or overwrite it.

---

11. COMPARABLE QUALITY SCORE

Each comparable receives a deterministic quality score.

Recommended weighting:

- Property type similarity: 20%
- Distance: 20%
- Sale recency: 20%
- Size similarity: 15%
- Beds/Baths similarity: 10%
- Year built: 10%
- Other relevant characteristics: 5%

Total:

"100%"

The weighting must be configurable in backend configuration.

The engine MUST store the score and the factors contributing to it.

---

12. OUTLIER DETECTION

The engine MUST identify abnormal comparable prices.

Possible methods include:

- Median-based deviation
- Interquartile range
- Z-score
- Configurable price-per-square-foot thresholds

Outliers MUST NOT automatically be deleted.

Instead, classify them:

- "NORMAL"
- "POTENTIAL_OUTLIER"
- "OUTLIER"

The system should explain why a comp was classified as an outlier.

---

13. WEIGHTED COMPARABLE VALUE

Qualified comparables are weighted according to their quality scores.

General formula:

"Weighted Comp Value = Σ(Comparable Value × Comparable Weight) / Σ(Comparable Weight)"

Comparable weights MUST be deterministic.

The engine must retain the individual comparable contributions.

---

14. ARV — AFTER REPAIR VALUE

ARV represents the estimated market value of the property after appropriate repairs/improvements.

Primary methodology:

1. Identify qualified sold comparables.
2. Score comparable quality.
3. Remove or reduce influence from confirmed outliers.
4. Calculate weighted comparable value.
5. Produce ARV.
6. Calculate ARV confidence.

Default:

"ARV = Weighted Comparable Value"

unless a documented market-adjustment methodology is implemented.

---

15. ARV CONFIDENCE

ARV confidence must consider:

- Number of qualified comps
- Comparable quality
- Geographic proximity
- Sale recency
- Size similarity
- Price dispersion
- Data completeness
- Outlier presence

Possible classifications:

- "HIGH"
- "MEDIUM"
- "LOW"
- "INSUFFICIENT_DATA"

The system MUST NOT report a high-confidence ARV when comparable evidence is weak.

---

16. EQUITY

When verified market value and debt information are available:

"Equity = Estimated Market Value - Outstanding Debt"

If debt information is unavailable:

"Equity = UNKNOWN"

Do not assume the mortgage balance is zero.

---

17. REPAIR COST

Repair cost can originate from:

A. User Input

A user-provided repair budget is classified as:

"USER_INPUT"

B. AI Estimate

An AI-generated estimate is classified as:

"AI_ESTIMATE"

C. Verified/External Estimate

A value retrieved from an approved data source is classified as:

"SOURCE_DATA"

The source classification MUST be preserved.

The AI MUST NOT present an AI repair estimate as a verified contractor quote.

---

18. MAO — MAXIMUM ALLOWABLE OFFER

MAO must be configurable.

Default strategy:

"MAO = ARV × MAO_PERCENTAGE - REPAIR_COST - DESIRED_PROFIT"

Where:

- "ARV" = deterministic ARV
- "MAO_PERCENTAGE" = configured investment strategy parameter
- "REPAIR_COST" = selected repair-cost input
- "DESIRED_PROFIT" = configured target profit

The percentage MUST NOT be hard-coded into the AI.

It must come from backend configuration or user strategy settings.

---

19. WHOLESALE SPREAD

For wholesale analysis:

"Wholesale Spread = Expected Assignment Price - Purchase Contract Price"

Where applicable:

"Expected Assignment Price = MAO or target investor purchase price"

The exact contract and assignment values must come from actual deal inputs.

Do not invent an assignment price.

---

20. WHOLESALE MARGIN

When valid purchase and assignment values exist:

"Wholesale Margin % = Wholesale Spread / Purchase Contract Price × 100"

If the denominator is zero or unavailable:

"UNKNOWN"

---

21. FLIP PROFIT

Basic deterministic model:

"Flip Profit = Expected Sale Price - Purchase Price - Repair Cost - Transaction Costs - Holding Costs - Financing Costs - Other Costs"

Each cost component must be explicitly represented.

Missing costs must not automatically be treated as zero unless the configuration explicitly defines them as zero.

---

22. ROI

When applicable:

"ROI % = Net Profit / Total Invested Capital × 100"

Total invested capital must be explicitly defined by the selected investment strategy.

Do not calculate ROI when required inputs are unavailable.

Return:

"UNKNOWN"

instead of fabricating missing values.

---

23. RENTAL POTENTIAL

Rental analysis may include:

- Estimated monthly rent
- Gross rental yield
- Operating expenses
- NOI
- Cap rate
- Cash flow

These values must be calculated from available data.

If rental data is unavailable, return:

"UNKNOWN"

The system MUST distinguish:

- Verified rental data
- User input
- AI estimate

---

24. PRICE VS COMPS

Calculate the subject property's price relative to comparable market value.

Example:

"Price vs Comps % = (Asking Price - Weighted Comp Value) / Weighted Comp Value × 100"

Interpretation must be configurable.

Possible classifications:

- "BELOW_MARKET"
- "AT_MARKET"
- "ABOVE_MARKET"

---

25. PRICE VS ARV

Calculate:

"Price vs ARV % = Asking Price / ARV × 100"

This metric helps determine how close the current asking price is to estimated post-repair value.

---

26. MOTIVATED SELLER SIGNALS

Motivated-seller analysis is a signal system, not proof.

Possible signals:

- Long time on market
- Price reductions
- Distress indicators
- Vacant property
- Tax delinquency
- Foreclosure indicators
- Absentee ownership
- Probate indicators where legally available
- Code violations
- High equity
- Expired/canceled listing
- Ownership duration
- Property condition indicators

Each signal should be classified as:

- "VERIFIED"
- "POSSIBLE"
- "UNKNOWN"

The AI MUST NOT claim that a seller is motivated solely because a signal exists.

---

27. DEAL SCORE

The final Deal Score must be deterministic.

It may incorporate:

- Discount to market
- Discount to ARV
- Estimated profit
- ROI
- Repair burden
- Comparable confidence
- Seller motivation signals
- Market conditions
- Data confidence
- Risk

Every scoring factor must have a defined weight.

Total score:

"0–100"

The scoring configuration must be stored in backend configuration.

---

28. DATA CONFIDENCE PENALTY

The engine MUST penalize deals where critical data is incomplete or unreliable.

Potential penalties:

- Missing ARV evidence
- Weak comps
- Missing repair information
- Missing debt information
- Unverified ownership data
- Stale market data
- Conflicting records

The exact penalty values must be configurable.

---

29. RISK SCORE

Risk should increase when:

- Data confidence is low
- Comparable dispersion is high
- Repairs are uncertain
- Property information is incomplete
- Asking price is significantly above supported value
- Market liquidity is weak
- Transaction assumptions are incomplete

Risk classification:

- "LOW"
- "MEDIUM"
- "HIGH"
- "CRITICAL"

---

30. FINAL DEAL CLASSIFICATION

The engine should classify a property using deterministic rules.

Possible classifications:

EXCELLENT DEAL

Strong financial metrics, strong comparable evidence, and acceptable risk.

GOOD DEAL

Positive investment characteristics with manageable uncertainty.

MARGINAL DEAL

Potential opportunity but insufficient margin or elevated uncertainty.

PASS

Risk/reward does not justify the deal based on available evidence.

INSUFFICIENT DATA

There is not enough reliable data to make a responsible classification.

The final classification MUST be explainable.

---

31. EXPLAINABILITY

Every final score should provide a breakdown.

Example structure:

Deal Score: 91/100

Positive Factors:
- Asking price below supported market value
- Strong comparable evidence
- Attractive projected wholesale spread
- Strong seller motivation signals

Negative Factors:
- Repair estimate has medium confidence
- One major comparable was excluded as an outlier

Risk:
MEDIUM

Data Confidence:
HIGH

Final Classification:
EXCELLENT DEAL

The explanation must reflect actual engine outputs.

---

32. AI AGENT RESPONSIBILITIES

The AI agent MAY:

- Explain calculations
- Summarize property data
- Explain comparable selection
- Explain deal scores
- Generate investor-facing summaries
- Identify qualitative patterns
- Generate outreach drafts
- Answer questions about calculated results

The AI agent MUST NOT:

- Invent financial values
- Override backend calculations
- Change formulas
- Change scoring weights
- Select arbitrary comps against engine rules
- Present estimates as facts
- Hide missing data
- Claim certainty when confidence is low

---

33. BACKEND RESPONSIBILITIES

The backend MUST:

- Perform calculations
- Validate inputs
- Apply scoring rules
- Apply confidence rules
- Apply risk rules
- Store calculation inputs
- Store calculation outputs
- Preserve data provenance
- Return deterministic results
- Expose structured results to the AI layer

---

34. AUDITABILITY

For each calculated result, the system should be able to answer:

- What input data was used?
- Where did the data come from?
- What formula was used?
- What configuration was active?
- Which comparables were selected?
- Which comparables were excluded?
- Why were they excluded?
- What confidence level was assigned?
- What risk factors were identified?

The calculation process must be reproducible.

---

35. ERROR HANDLING

If required data is missing:

Do NOT fabricate.

Return a structured state such as:

"INSUFFICIENT_DATA"

If an external data source fails:

"DATA_SOURCE_ERROR"

If calculation inputs are invalid:

"INVALID_INPUT"

If data conflicts:

"DATA_CONFLICT"

---

36. CONFIGURATION

The following MUST be configurable rather than hard-coded:

- Comparable radius
- Sale recency windows
- Size tolerance
- Bed/bath tolerance
- Year-built tolerance
- Comparable scoring weights
- Outlier thresholds
- MAO percentage
- Desired profit
- Transaction costs
- Holding costs
- Financing assumptions
- Deal-score weights
- Risk thresholds
- Confidence thresholds

Configuration changes must not require changing the AI prompt.

---

37. RESULT SCHEMA

A deal-analysis result should conceptually contain:

{
  "property": {},
  "market_value": {},
  "comparables": [],
  "arv": {},
  "repair_cost": {},
  "equity": {},
  "mao": {},
  "wholesale": {},
  "flip": {},
  "rental": {},
  "motivation_signals": [],
  "deal_score": {},
  "risk_score": {},
  "data_confidence": {},
  "classification": {},
  "explanation": {}
}

The exact production schema must follow the project's technical specification and database implementation.

---

38. SOURCE-OF-TRUTH RULE

If the AI agent, frontend, backend, or another document conflicts with this document regarding deterministic deal-analysis calculations, this document takes precedence.

No AI-generated response may override the deterministic engine.

Any proposed modification to these rules must be explicitly approved and documented.

---

39. FINAL SYSTEM RULE

SCALEESTATE AI must follow this principle:

DATA → NORMALIZATION → DETERMINISTIC CALCULATION → CONFIDENCE/RISK → DEAL CLASSIFICATION → AI EXPLANATION

Never:

DATA → AI GUESS → FINANCIAL RESULT

The AI explains the numbers.

The deterministic engine owns the numbers.