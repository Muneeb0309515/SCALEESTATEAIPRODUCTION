# Property-detail validation

Validated on 2026-08-31 in the signed-in SCALEESTATE AI workspace.

A live search result for provider property ID `9287164194` was opened with the source address `5619 Walnut Hill Ln, Dallas, TX 75229`. The property-intelligence screen initially showed a loading state, then resolved a source-backed RealtyAPI.io record.

Observed verified fields: address `5619 Walnut Hill Ln, Dallas, TX 75229`, property type `single_family`, 10 beds, 27,092 sf, listing status `for_sale`, list price `$64,000,000`, provider `realtyapi`, and retrieval timestamp `8/31/2026, 5:38:08 AM`. Baths and days on market remained `UNKNOWN` because the provider response did not supply them. No owner, comparable-sales, ARV, or other unverified values were fabricated.

The unresolved-record behavior was caused by the search result link carrying only the provider ID while the existing intelligence screen read only local organization records. The fix passes the provider address through the link, adds a protected provider-detail route, and hydrates the detail screen from RealtyAPI.io using the authenticated bearer token and organization header.
