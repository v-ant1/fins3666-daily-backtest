# Normalized numeric design extract for K1

This file normalizes numeric preregistration terms for the preregistration-diff parser. The authoritative design text is `specs/r6_prereg/K1.md`; the synthetic tests assert runtime facts the parser cannot represent (including `K=min(5,floor(n/2))`, the exact 5/30 reference fraction, and the full manifest hash).

- horizon=21.
- NW lag 4.
- t≥2.
- turnover cap=0.50.
- cost 0.05% per side.
- top_fraction=0.16666666666666666; top 5 names.
- 500 placebo draws; 5000 bootstrap draws.
- 95th percentile placebo threshold.
- seed=20261111.
- block length 10 sessions.
- active_share_min=0.50.
- p<0.05 and p<0.10.
- return_dispersion=0.10.

## Registered endpoints

1. H16 mechanism.
2. H17 placebo.
3. H18 portfolio.
