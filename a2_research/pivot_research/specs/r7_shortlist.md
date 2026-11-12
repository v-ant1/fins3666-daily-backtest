# R7 shortlist gate

**Decision: no directions shortlisted; idea generation is not authorized yet.** This is a gate-status record, not a literature screen or preregistration.

## Five-minute prerequisite check

| Check | Finding | Decision |
|---|---|---|
| Power gate | `report_drafts/R7_POWER_GATE.md` is absent at the specified path. | **Fail / pending.** R6 workflow review §5 requires a GO before full idea screening. Do not start candidate searches until the gate is documented as GO. |
| Data inventory | `specs/R7_DATA_MANIFEST.md` is absent. The R6 fallback contains multiple source-specific manifests, but without a candidate and a consolidated R7 inventory they do not establish R7 S&P 500 point-in-time coverage, delisting treatment, tradability, or a sealed comparable holdout. | **Pending.** L1's manifest is a prerequisite to a candidate-specific data check. |
| Duplicate index | `specs/r6_screened_index.md` is present and lists prior screen families plus the seven frozen directions D1, E1, G1, J1, K1, P1, and R1. | **Checked.** None of those seven can be represented as a new discovery. A universe change is permitted by R6 workflow review §§1 and 4 only as a separated R7 strategy with a fresh preregistration; it does not itself create a distinct pressure mechanism. |
| Candidate literature/effects | No candidate was advanced to the two-paper/effect-size check. | **Not run.** Under §§5–6, a missing power GO ends screening; collecting candidate literature now would bypass that gate. |

## Next action

Wait for L1's `specs/R7_DATA_MANIFEST.md` and L2's `report_drafts/R7_POWER_GATE.md`. If L2 records **GO**, screen at most two mechanisms in bounded checks against the duplicate index, two verified papers, manifest support (using R6 manifests only as a provisional fallback), and published effect sizes versus the gate. If the gate is not GO, retain an empty shortlist and document the no-go; do not relabel a frozen R6 strategy as new.
