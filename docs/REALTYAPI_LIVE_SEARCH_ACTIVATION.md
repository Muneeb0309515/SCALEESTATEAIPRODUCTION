# RealtyAPI.io Live Search Activation

## Current behavior

The RealtyAPI.io adapter is configured server-side and the property-search route is implemented at `/api/v1/providers/property-search` (also available as `/api/v1/search-us-market`). The route is intentionally protected by the project authentication boundary. In standalone preview, the route returns `503 CONFIGURATION_REQUIRED` because `SUPABASE_PROJECT_VALIDATED` is not set. This is a deliberate fail-closed state; the application must not expose provider access or organization data without authenticated scope.

The search page now provides selectable property category, listing status, maximum price, and minimum-bed filters. It submits those values to the provider route, shows a bounded loading state, and renders the authentication-required message with an access-state action when the standalone boundary rejects the request.

## Activation requirements

The approved runtime configuration must provide a valid HTTPS Supabase URL, a server-side Supabase key, and `SUPABASE_PROJECT_VALIDATED=true`. These values must be configured through the project secret-management workflow; they must not be committed to source control or exposed in browser code.

After authentication is activated, the frontend session bridge must provide the authenticated Supabase access token to the FastAPI route as `Authorization: Bearer <access-token>`. Organization-scoped routes additionally require a verified organization membership boundary. The current standalone sign-in page is informational only and does not claim that authenticated UI access is active.

## Verification sequence

1. Confirm the project uses the intended Supabase project and that the organization-membership schema and RLS policies are applied.
2. Set `SUPABASE_PROJECT_VALIDATED=true` through project configuration after the project has been validated.
3. Sign in through the approved Supabase Auth flow and obtain a valid access token for the test user.
4. Call the property-search route with `Authorization: Bearer <access-token>` and a query such as `location=Austin%2C%20TX&property_type=single_family&limit=3`.
5. Confirm the response contains only normalized provider records and retains `source: realtyapi`, `data_updated_at`, `provider_property_id`, and the requested result limit.
6. Confirm the browser search form sends the selected category and displays provider-backed results. If authentication is missing, the expected result is the explicit access-state error rather than fabricated or cached data.

## Automated coverage

`backend/tests/test_property_search_integration.py` verifies the protected route with controlled authenticated identity and a provider fixture. `scripts/search-browser-check.mjs` verifies that a real browser submits the category filter and renders the standalone authentication-required state. These tests do not seed production property records or claim that standalone preview has live organization access.
