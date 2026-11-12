# Round 4 trial log (budget: 30 variants)

| # | Approach | Variant | Pre-reg file | Date | Result |
|---|---|---|---|---|---|
| 1 | D5 | variant 1 primary five-session follower IC | specs/r4_prereg/D5.md | 2026-11-10 | FAIL: mean_IC=0.0074551336; NW_t=0.56437766; one_sided_p=0.28624857 |
| 2 | D5 | reverse-edge mean IC placebo | specs/r4_prereg/D5.md | 2026-11-10 | PASS: mean_IC=-0.0014451714; NW_t=-0.075924969; two_sided_p=0.93947879 |
| 3 | D5 | within-SIC permuted leader comparison | specs/r4_prereg/D5.md | 2026-11-10 | FAIL: null_p95=0.015677289; randomization_p=0.30738523; observed_percentile=0.694; pooled_null_NW_t=0.48790415 |
| 4 | D5 | fixed 20-session shifted graph placebo | specs/r4_prereg/D5.md | 2026-11-10 | PASS: mean_IC=-0.0042495024; NW_t=-0.3052078; two_sided_p=0.76020789 |
| 5 | D5 | variant 2 60-session sensitivity follower IC | specs/r4_prereg/D5.md | 2026-11-10 | REPORTED: mean_IC=0.0037021994; NW_t=0.26753946; one_sided_p=0.39452692; reported sensitivity, not advanced |
| 6 | D6 | D6-1 primary 12-minus-1 bond-to-SPY mechanism | specs/r4_prereg/D6.md | 2026-11-11 | D6-1: beta=0.076921251; NW_t=0.76634416; one_sided_p=0.22173578; gate=False |
| 7 | D6 | D6-2 12-1 SPY-to-Treasury | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.001568736; NW_SE=0.020571542; NW_t=0.07625758; one_sided_p=0.53039291 |
| 8 | D6 | D6-3 12-1 observed vs circular shift | specs/r4_prereg/D6.md | 2026-11-11 | observed_beta=0.076921251; null_p95=0.094980764; percentile=0.946; randomization_p=0.055888224 |
| 9 | D6 | D6-4 six-minus-one bond-to-SPY | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.33798953; NW_SE=0.12884472; NW_t=2.6232315; one_sided_p=0.0043550034; sensitivity only |
| 10 | D6 | D6-5 six-minus-one SPY-to-Treasury | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.048030285; NW_SE=0.040972639; NW_t=1.1722527; one_sided_p=0.87945218; sensitivity only |
| 11 | D6 | D6-1 primary 12-minus-1 bond-to-SPY mechanism | specs/r4_prereg/D6.md | 2026-11-11 | D6-1: beta=0.076921251; NW_t=0.76634416; one_sided_p=0.22173578; gate=False |
| 12 | D6 | D6-2 12-1 SPY-to-Treasury | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.001568736; NW_SE=0.020571542; NW_t=0.07625758; one_sided_p=0.53039291 |
| 13 | D6 | D6-3 12-1 observed vs circular shift | specs/r4_prereg/D6.md | 2026-11-11 | observed_beta=0.076921251; null_p95=0.094980764; percentile=0.946; randomization_p=0.055888224 |
| 14 | D6 | D6-4 six-minus-one bond-to-SPY | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.33798953; NW_SE=0.12884472; NW_t=2.6232315; one_sided_p=0.0043550034; sensitivity only |
| 15 | D6 | D6-5 six-minus-one SPY-to-Treasury | specs/r4_prereg/D6.md | 2026-11-11 | beta=0.048030285; NW_SE=0.040972639; NW_t=1.1722527; one_sided_p=0.87945218; sensitivity only |
| 16 | D4 | D4-1 primary IC | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.018073999; NW_t=-2.4194916; raw_p=0.99222889; gate=False |
| 17 | D4 | D4-2 degree-preserving comparison | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.018073999; NW_t=-2.4194916; raw_p=0.95608782; null_p95=0.0064596824; gate=False |
| 18 | D4 | D4-3 random-link comparison | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.018073999; NW_t=-2.4194916; raw_p=0.97804391; null_p95=0.0092156939; gate=False |
| 19 | D4 | D4-4 fixed 20-session shift comparison | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.0022544337; NW_t=-0.62456135; raw_p=0.7338705; gate=False |
| 20 | D4 | D4-5 degree placebo equivalence | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.0056278616; raw_p=0.48573705; CI90=[-0.012165892,0.000910169]; p95_abs=0.017069057; gate=False |
| 21 | D4 | D4-6 random-link placebo equivalence | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.0033827014; raw_p=0.17794169; CI90=[-0.0076359474,0.00087054464]; p95_abs=0.016024223; gate=False |
| 22 | D4 | D4-7 shifted placebo equivalence | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.015819565; raw_p=0.91798249; CI90=[-0.027697784,-0.0039413465]; p95_abs=0.015819565; gate=False |
| 23 | D4 | D4-8 variant-2 IC | specs/r4_prereg/D4.md | 2026-11-11 | mean_IC=-0.0068366695; NW_t=-0.78820026; raw_p=0.78471021; diagnostic_only=true |
| 24 | J1 | J1-V1 weekly SIC2-relative reversal | specs/r4_prereg/J1.md | 2026-11-11 | FAILED: ValueError: held Dow name lacks a close price |
| 25 | J1 | J1-V1 weekly SIC2-relative reversal | specs/r4_prereg/J1.md | 2026-11-11 | FAILED: ValueError: L3 relative-return signal mismatch at dow 2026-06-29 AAPL |
| 26 | J1 | J1-V1 weekly SIC2-relative reversal | specs/r4_prereg/J1.md | 2026-11-11 | J1-V1: mechanism=True; mean_raw_IC=-0.01478633328; direction_adjusted_NW_t=2.0770416; portfolio=False |
| 27 | K1 | K1-V1 | specs/r4_prereg/K1.md | 2026-11-11 | K1-V1: status=portfolio_not_run; prereg=889a6ffa50fe65864b0c432e1590c2252b7f2a76de6f914bafbdf2578441d3b3 |

## Holdout integrity log
- 2026-11-10: L4 (data scout) accidentally saw rendered DWDP historical OHLCV rows on ChartExchange while checking availability. No values were computed or used. Ruling: L4 is excluded from all hypothesis, pre-registration and implementation work for the rest of the goal. The DWDP membership window (2017-09 to 2019-04) is flagged in the holdout and must be reported as a robustness exclusion (holdout run both with and without that window). No other worker saw it.

## Freeze log
- D5 FROZEN 2026-11-10 by the coordinator (D5 input QA passed: 11 directed pairs on 293/293 dates). Pre-freeze fix: the time-shift placebo clarified as one fixed 20-session shift (decision 7).

## Holm family manifest (goal-wide; endpoints added BEFORE their outcomes are computed)
- D5: endpoints (1)-(6) as enumerated in specs/r4_prereg/D5.md
- D4: endpoints (1)-(9) as enumerated in specs/r4_prereg/D4.md (added at the D4 freeze)

## Freeze: D6 (2026-11-10), SHA256 341a406f0de406a989bc3fe6195de08f127592f011e7bd975eb1519bd71949dd
Holm manifest additions, D6 endpoints 1-6:
- D6-1: 12-1 bond->SPY beta > 0
- D6-2: 12-1 SPY->Treasury beta < 0
- D6-3: observed vs circular-shift placebo
- D6-4: 6-1 bond->SPY > 0
- D6-5: 6-1 SPY->Treasury < 0
- D6-6: net portfolio excess vs EW5

## Freeze: D4 (2026-11-10), SHA256 ff169ae4e5339364a400b8bec85e9251c77862923dc94c0049f23d79a9059421
Holm manifest additions, D4 endpoints 1-9:
- (1) v1 NCP IC
- (2-4) degree-preserving, random-link and 20-session-shift randomization tests
- (5-7) placebo equivalence tests
- (8) v2 IC (inferential)
- (9) v1 portfolio net excess vs EW30
Full family = D5 1-6 + D6 1-6 + D4 1-9 = 21 endpoints.

NOTE (coordinator): D6 rows 6-10 (accidental L1 run) and 11-15 (official L2 run) are identical; they count ONCE in the Holm family.

## R6 Holm family (separate from R5; fixed before outcomes)
### Freeze: D1 (2026-11-11), SHA256 d5059ac49ba2d2d4c5450c01632011a9f3a673dc1e8de7821d9713d6cb9ac26e
- R6 variant 1: D1-V1
- R6-H1 D1-1: S&P 500 mean IC of negative short pressure > 0 (NW one-sided)
- R6-H2 D1-2: SIC2-stratified shuffle placebo (randomization one-sided)
- R6-H3 D1-3: Dow portfolio net excess vs EW30 (block bootstrap one-sided)
### Freeze: E1 (2026-11-11), SHA256 3d36d0528c14d3590fa881c6b59af5aefdddb80c876ec8705cfd0b62201a67d9
- R6 variant 2: E1-V1
- R6-H4 E1 mechanism: S&P 500 monthly IC > 0 (NW lag 20), with floor 0.001155
- R6-H5 E1 SIC2-preserving shuffle placebo
- R6-H6 E1 Dow portfolio net excess vs EW30
### Freeze: J1 (2026-11-11), SHA256 996b971090be395fffb1e11dff1430bbf581b338637250716607bf6b51cb7698
- R6 variant 3: J1-V1
- R6-H7 J1 S&P mechanism (direction-adjusted NW lag 4, floor 0.003464)
- R6-H8 J1 SIC2 label shuffle placebo
- R6-H9 J1 Dow portfolio net excess vs EW30
### Freeze: R1 (2026-11-11), SHA256 3df293c87ff8eaf446a90d089bfe7672606bf7df7b26701b86b8f98c9c5955b0
- R6 variant 4: R1-V1
- R6-H10 R1 S&P mechanism (SIC2-stratified payer spread > 0, NW lag 3)
- R6-H11 R1 within-SIC2 payer-flag shuffle placebo
- R6-H12 R1 Dow portfolio net excess vs EW30
### Freeze: P1 (2026-11-11), SHA256 939e8272c4487b7728e1e4993ce62acee9e71134b5cabbe7417e16a2e9e3e3bc
- R6 variant 5: P1-V1
- R6-H13 P1 S&P mechanism (sign + NW t≥2)
- R6-H14 P1 SIC2 shuffle placebo
- R6-H15 P1 Dow portfolio net excess vs EW30

- K1-V1 FROZEN 2026-11-11 SHA 889a6ffa50fe65864b0c432e1590c2252b7f2a76de6f914bafbdf2578441d3b3 (R6-H16..H18)

- G1-V1 FROZEN 2026-11-11 SHA 201c2c95137ac3fc0ce139eb539837c823431a74b8959f68a6efd2ddb4bef4e6 (R6-H19..H21)
