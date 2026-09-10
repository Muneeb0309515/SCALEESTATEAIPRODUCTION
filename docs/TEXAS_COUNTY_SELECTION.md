# SCALEESTATE AI Texas County Selection

**Phase:** 2 — Texas Real-World Benchmark and End-to-End Workflow  
**Recommendation:** **Travis County** and **Bexar County**  
**Selection date:** 2026-09-10  
**County names are benchmark configuration, not core business logic.**

## Recommendation

Select **Travis County** and **Bexar County** as the two initial benchmark counties. Together they provide the strongest combination of directly usable acquisition-source data and observable resale-market validation among the counties reviewed.

Travis County is the primary benchmark because its official tax office publishes a daily-refresh delinquent-tax CSV. The retrieved source reported **8,258 tax-account rows** and approximately **$81.42 million total due** on September 9, 2026. The source explicitly warns that the file is a working document, includes multiple property types, and is not a delinquency-rate denominator. Travis also has detailed MLS-based sales, inventory, and close-to-list reporting through Unlock MLS.

Bexar County is the complementary benchmark because its official foreclosure-notice publication provides a directly countable notice workflow. The retrieved October 2026 list contained **344 entries: 327 mortgage notices and 17 tax notices**. These are notices, not completed foreclosures or necessarily unique properties. Bexar also provides a large resale-market proxy through MLS/listing data.

No reviewed county has an authoritative public county-level series for assignment volume, wholesale contracts, cash-buyer depth, investor bid spreads, or wholesale close rates. Ordinary sales, days on market, sale-to-list ratios, tax accounts, and foreclosure notices are therefore treated as **workflow or exit-liquidity proxies**, never as measured wholesaling activity.

## Comparative evidence

| Criterion | Travis County | Bexar County |
|---|---|---|
| Tax delinquency | **FACT:** official daily-refresh CSV; 8,258 rows and approximately $81.42M total due in the retrieved snapshot. **LIMITATION:** working file, multiple property types, not a delinquency rate. | **FACT:** official tax-sale process; 17 tax notices in the retrieved October 2026 notice list. **LIMITATION:** notice count is not total delinquent inventory. |
| Foreclosure | **FACT:** official tax-sale and searchable non-tax foreclosure processes. **UNAVAILABLE:** no stable countywide count extracted. | **FACT:** official October 2026 list contained 327 mortgage notices and 17 tax notices. **LIMITATION:** notices are not completed foreclosures or unique properties. |
| Distressed inventory | **PROXY:** tax-account file is a screening universe, not residential distressed inventory. | **PROXY:** official notice list is a distress pipeline, not a unique-property inventory. |
| Investor activity | **UNAVAILABLE/PROXY:** no verified county-level investor-purchase share. | **PROXY:** San Antonio metro institutional-investor share reported at 9.5% for 2024; not a Bexar County statistic. |
| Wholesaling liquidity | **PROXY:** MLS sales, inventory, and close-to-list data indicate ordinary exit depth, not assignment activity. | **PROXY:** large listing base and resale activity indicate ordinary exit depth, not assignment activity. |
| FSBO/off-market opportunity | **UNAVAILABLE** as a validated countywide series. | **UNAVAILABLE** as a validated countywide series. |
| Migration/churn | **FACT:** 7.7% population growth from the 2020 estimates base; **PROXY:** 18.7% did not live in the same house one year earlier. | **FACT:** 7.5% population growth from the 2020 estimates base; **PROXY:** 16.5% did not live in the same house one year earlier. |
| Transaction liquidity | **FACT/PROXY:** 13,217 MLS sales in 2025, 76,206 active listings, 3.9–4.2 months of inventory in cited snapshots. | **PROXY:** 18,290 active listings, 60 median days on market, and 99% sale-to-list in the cited snapshot. |
| Data confidence | **MEDIUM:** strongest operational tax file, but limitations require parcel/property-type validation. | **MEDIUM:** strong notice-list evidence, but notice deduplication and completion status require validation. |

## County classifications

### Travis County

- **FACT:** The Travis County Tax Office publishes a delinquent-tax CSV with a source modification date and property/account fields.
- **CALCULATED:** The retrieved file contained 8,258 rows and approximately $81.42 million in total due.
- **PROXY:** The file is a tax-distress screening universe, not a residential delinquency rate or confirmed motivated-seller list.
- **FACT:** Unlock MLS reported 13,217 MLS residential sales in 2025, 76,206 active listings, and 4.2 months of inventory in December 2025.
- **INFERENCE:** Travis supports testing tax-distress ingestion, property classification, source freshness, and mainstream exit-liquidity analysis.

### Bexar County

- **FACT:** The Bexar County Clerk publishes a current foreclosure-notice list and foreclosure map for mortgage and tax notices.
- **CALCULATED:** The retrieved October 2026 list contained 344 entries: 327 mortgage and 17 tax notices.
- **PROXY:** Notice entries represent a sourcing pipeline, not completed foreclosures or necessarily unique properties.
- **PROXY:** San Antonio metro institutional-investor activity is not equivalent to Bexar County investor activity.
- **INFERENCE:** Bexar supports testing notice extraction, mortgage-versus-tax signal separation, duplicate handling, source timestamps, and resale-market context.

## Sources

1. [Travis County Tax Office — Property Tax Reports and Data](https://tax-office.traviscountytx.gov/about-us/reports-data/property-taxes) — official source and refresh guidance.
2. [Travis County Delinquent Tax Open Data](https://tax-office.traviscountytx.gov/voterdata/TaxDelqOpenData.csv) — official property/account-level working file.
3. [Travis County Tax Office — Foreclosed Properties](https://tax-office.traviscountytx.gov/properties/foreclosed) — official tax-sale process.
4. [Travis County Constable Precinct 5 — Tax Sales](https://www.constable5.com/tax-sales/) — official process details.
5. [U.S. Census QuickFacts — Travis County](https://www.census.gov/quickfacts/fact/table/traviscountytexas/PST045225) — population, housing, and same-house measures.
6. [Unlock MLS — December 2025 Central Texas Housing Report](https://www.unlockmls.com/news/december-2025-central-texas-housing-report) — Travis market activity proxy.
7. [Unlock MLS — January 2026 Central Texas Housing Report](https://www.unlockmls.com/news/january-2026-central-texas-housing-report) — current market activity proxy.
8. [Bexar County — Public Sale of Property](https://www.bexar.org/1587/Public-Sale-of-Property-PDF) — official tax-sale process.
9. [Bexar County — Foreclosure Notices](https://www.bexar.org/foreclosure-notices) — official foreclosure-notice source.
10. [Bexar County Foreclosure Map](https://maps.bexar.org/foreclosures/) — official mortgage/tax notice workflow.
11. [U.S. Census QuickFacts — Bexar County](https://www.census.gov/quickfacts/fact/table/bexarcountytexas/PST045225) — population, housing, and same-house measures.
12. [Realtor.com — Bexar County Market](https://www.realtor.com/local/market/texas/bexar-county) — clearly labeled MLS/listing-market proxy.
13. [Axios San Antonio — Institutional Investors](https://www.axios.com/local/san-antonio/2025/03/03/investors-buying-real-estate-homes) — metro-level investor proxy; not a Bexar County fact.
14. [Texas Real Estate Research Center — Bexar County Housing Activity](https://trerc.tamu.edu/housing-activity-data/county/bexar-county/) — MLS coverage limitations and market context.

## Benchmark guardrails

The application must not hard-code Travis or Bexar into core property, analysis, or scoring logic. The selected counties belong in benchmark configuration and data manifests only. The benchmark must preserve source URLs, source timestamps, field provenance, signal evidence, and explicit unknown states. It must not create fake properties to reach a target count.
