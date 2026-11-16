# D7 input-only feasibility QA

**Gate verdict: {{GATE_STATUS}}**

This report uses SEC filing/link metadata, the D7 event clock, point-in-time Dow membership, and dated two-digit SIC values only. It contains no adjusted prices, customer event returns, supplier forward returns, ICs, regressions, or portfolio results. The event/link tables are built from development dates **2020-11-27 through 2026-10-30**. Any failure is final for this pre-outcome gate; do not inspect outcomes to decide whether to continue.

## Frozen input-only thresholds

| Gate item | Required | Observed | Status |
|---|---:|---:|---|
| Distinct response dates with at least 3 active, linked Dow supplier recipients | ≥30 | {{EVENT_DATES}} | {{GATE1_STATUS}} |
| Distinct directed Dow customer→supplier pairs usable on a qualifying response date | ≥10 | {{PAIR_COUNT}} | {{GATE2_STATUS}} |
| Qualifying dates with all customer SIC buckets shuffleable using eligible alternate suppliers | 100% | {{SHUFFLE_COVERAGE}} | {{GATE3_STATUS}} |

### Gate record

```json
{{GATE_JSON}}
```

## Response-date coverage

| Response date | Event customers | Active linked suppliers | Cumulative usable directed pairs | Recipients without point-in-time SIC | Shuffle pool |
|---|---:|---:|---:|---:|---|
{{DATE_COVERAGE}}

## Event-clock checks

The event table reports `filing_date`, normalized `acceptance_timestamp_et` and `acceptance_timestamp_utc`, `release_timestamp_et` when explicitly supplied from the furnished exhibit, normalized release/acceptance fields, `f`, `a`, final `response_session`, and the event's source URLs. With an explicit exhibit time, `a` is the first NYSE open strictly later than the later known release/acceptance time and `d=max(f,a)`. When exhibit release time is unknown, the preregistered exception sets `d=f`; acceptance is retained for the audit trail and is not used as a replacement release time.

The current `earnings_clock.csv` schema has no release-time or exhibit-specific URL column. The builder accepts an optional reviewed annotation CSV with `customer_cik`, `accession_number`, `release_timestamp_et`, and `exhibit_source_url`. If no annotation is supplied, it leaves `release_timestamp_et` blank and records the filing URL separately; it reports that limitation below. No release time is inferred from the BMO/intraday/AMC acceptance classification.

First five rows of the derived event table:

```json
{{EVENT_EXCERPT}}
```

## Input audit counts and limitations

```json
{{QA_JSON}}
```

The source `LINKS.csv` and SEC earnings-clock files are metadata inputs only. The builder never loads a price panel. SIC records dated before 2020-06-01 are skipped before ticker or SIC values are examined, preserving the sealed pre-2020-06 Dow holdout while allowing an already-public SIC code to carry into the first development sessions. This report does not certify filing-text classification or ticker/CIK lineage beyond the fields and point-in-time roster checks recorded here; those remain coordinator review items.

