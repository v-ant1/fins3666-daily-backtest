# S2 pooled S&P index flow — IDX4 development

**Tag:** L-IDX4. **Status: exhausted / no preregistration drafted.** The sole registered measurement did not produce development statistics or holdout coverage counts, so the primary net mean could not clear the specified MDE gate. No holdout price or return values were displayed or used for calculations.

## Frozen event metadata

Before any Alpaca request, `event_list_metadata.csv` was frozen (SHA-256 `7a7420cf326d0abd081d9127b9a45694472bd562b265f5a620df9b1b19af2f00`). It contains 105 development S&P 500 additions from the supplied roster and 234 development S&P 400 additions with dated linked S&P DJI releases; the holdout list has 48 S&P 400 additions and no roster-sourced S&P 500 events. The supplied S&P 500 roster begins 2020-06-01. Of the S&P 400 rows whose effective dates fell in the requested windows, 191 holdout and one development event were dropped for lacking a linked/findable dated S&P DJI release; six holdout and 22 development additions were dropped as detected 500→400 migrations using the supplied roster. The underlying Wikipedia table has 610 added-ticker rows; 87 linked events fell outside the two same-window date rules.

The fixed holdout metadata cannot identify 500→400 transfers before June 2020 from the supplied S&P 500 roster, so the historical holdout list may retain such transfers. This cannot be corrected after price access without violating the required fixed-universe-before-prices order.

## Measurement attempt

The run used the registered next-session-open to effective-date-close timing, Alpaca SIP `adjustment=all`, and the development PIT S&P 500 panel. A second identical process was accidentally launched while the first was still running and was stopped; both attempts are counted in the ledger. The surviving process ended without a summary JSON or event-return rows (the only return CSV is header-only), and the command wrapper did not retain its exception text. No further requests were made. Therefore N, mean, SD, median, confidence interval, index splits, cost-adjusted means, holdout covered N/missing percentage, and MDE are unavailable.

**Decision:** S2 exhausted for this run because the registered evidence gate was not demonstrated; no preregistration was created and no sealed holdout was opened.
