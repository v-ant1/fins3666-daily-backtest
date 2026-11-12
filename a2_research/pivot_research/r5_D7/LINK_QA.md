# D7 SEC customer-link input QA

Sample: SEC 10-K filings from 2019-01-01 through 2026-10-30; link-use window 2020-11-27 through 2026-10-30. This is an input-only build: no prices, returns, outcomes, or holdout data were read. SEC document bytes were downloaded from the public EDGAR Archives; company CIK/ticker references use the SEC company ticker directory and the supplied earnings clock.

## Extraction rules and limitations

The builder reads 10-K/10-K/A primary filing documents from SEC EDGAR. It accepts an explicitly named entity in either (a) a customer/sales sentence with an adjacent ≥10% claim or (b) a table where a uniquely matched company-name row is followed by an explicit percent-of-revenue row; for tables the first value is the current fiscal year. Anonymized labels and generic statements about “these customers” are not link identities. Unmatched or ambiguous candidates remain in `LINK_CANDIDATES.csv` for audit and are excluded from `LINKS.csv`; no SIC or industry relationship is inferred. Filing disclosures are usable from the first XNYS session strictly after the filing date. A later omission does not terminate a relationship; `valid_to` remains open because no explicit termination disclosure was machine-confirmed. Each link row retains its source accession, filing date and direct SEC URL. This conservative text parser is not a legal/accounting determination; source snippets need coordinator review before freeze.

## Counts

- Extracted disclosure candidates (including unmatched/ambiguous audit rows): 551.
- Eligible listed-name link rows in `LINKS.csv`: 19.
- Distinct named listed-customer/supplier pairs in `LINKS.csv`: 3.
- Distinct pairs where both customer and supplier are point-in-time Dow members on an overlapping development date, with the link already public: 0.
- Distinct directed pairs whose listed customer has at least one development earnings-clock filing: 0.
- Unique matched linked customers with a clock: 0.
- Matched, issuer-day-deduplicated 8-K Item 2.02 filings: 0; response dates under the preregistered unknown-time fallback with at least three active linked Dow recipients: 0; shuffleable dates: 0/0. The clock has no explicit earnings-release timestamp, so filing date is used only for the preregistered next-session fallback; the linked 8-K exhibits remain unaudited.
- SEC fetch/parse errors: 0.

| Year | Linked listed-customer Item 2.02 filings | Linked Dow-customer Item 2.02 filings |
|---:|---:|---:|
| 2020 | 0 | 0 |
| 2021 | 0 | 0 |
| 2022 | 0 | 0 |
| 2023 | 0 | 0 |
| 2024 | 0 | 0 |
| 2025 | 0 | 0 |
| 2026 | 0 | 0 |

## Frozen feasibility thresholds and verdict

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| Distinct event-response dates with ≥3 active linked Dow recipients | 30 | 0 | FAIL |
| Distinct directed Dow customer-supplier pairs | 10 | 0 | FAIL |
| Eligible alternate suppliers within PIT two-digit SIC for every qualifying date | 100% | 0/0 | FAIL |

Feasibility verdict: **INFEASIBLE — fixed metadata gate failed**. No outcomes, returns, or placebo draws were calculated.

## Audit files

- `LINKS.csv`: source rows with listed customer identity matches.
- `LINK_CANDIDATES.csv`: all parser candidates with snippet evidence, including unresolved names for manual audit.
- `EVENT_COVERAGE.csv`: metadata-only event-date, Dow-recipient, and SIC-shuffle feasibility counts.
- `SEC_FETCH_ERRORS.csv`: missing metadata/document downloads.
- `sec_cache/`: downloaded SEC submissions and filing documents, retained for reproducibility.
