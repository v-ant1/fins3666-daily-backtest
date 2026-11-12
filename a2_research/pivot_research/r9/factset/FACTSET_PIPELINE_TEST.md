# FactSet pipeline synthetic test

The builder was run against temporary synthetic CSV exports covering S&P and Dow memberships, an inactive security, a historical ticker change, an SEC acceptance date, one missing SIC, a split factor, and performance and merger delistings with missing returns.

Assertions passed for the 12 development-schema keys and their exact dtypes, aligned S&P/Dow date axes and roster shapes, strictly-next-session SIC2 availability, missing SIC remaining blank, stable security identity with the later ticker label, adjusted open from the split factor, -30% performance and 0% merger defaults, the 3% coverage-gate pass, and counts/coverage/SHA-256-only seal output. No real FactSet or holdout data was used; no panel was sealed from real exports because none are available.
