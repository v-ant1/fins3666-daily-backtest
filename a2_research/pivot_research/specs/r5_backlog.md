# R5 backlog

## Running
- L4: task_7cbd8785f7cc dated SIC panel + holdout 13F
- L2: task_d5ce1b4b25f6 finalise D4 prereg
- L3: task_0cdae41438fe finalise D5 prereg + D6 draft
- L1: task_ddd1e051290d D4 input QA + runner

## Next (in order, assigned as workers free up)
1. Coordinator freezes D4 (needs D4.md + INPUT_QA) -> L1 runs the D4 mechanism test + placebos
2. D5 input QA + runner (needs sic_panel + D5.md) -> coordinator freezes D5 -> D5 mechanism test
3. If mechanism passes: portfolio test (L1) -> coordinator holdout
4. Fillers: L2/L3 red-team each other's prereg; L2 drafts the report Testing section; L3 finalises D6 prereg; L4 checks the reproducibility of data builds
5. If D4/D5 fail: D6 freeze and test; then an L2/L3 research cycle
