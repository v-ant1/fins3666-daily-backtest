"""FINS3666 Phase 3 research harness."""
from .phase3 import (
    ICResult, EventStudyResult, PlaceboResult, PortfolioResult,
    cross_sectional_ic, event_study, network_placebos, newey_west_t,
    break_even_rank_ic,
    signal_matrix,
    portfolio_engine, circular_block_bootstrap_pvalue, holm_correction,
    deflated_sharpe_ratio, require_frozen_prereg, authorize_trial,
    append_trial, run_registered_trial, assert_future_truncation_invariant,
    run_holdout, prereg_digest, config_digest,
)
