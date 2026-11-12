"""Extract preregistered numeric design facts and compare them with a runner.

The checker intentionally focuses on numeric values attached to explicit
design terms (horizon, window, lag, seed, draws, costs, thresholds, etc.).
Runner configs use the same canonical keys; aliases such as ``seed`` and
``rng_seed`` are accepted. It fails closed when a fact in the preregistration
has no corresponding runner declaration or when values differ.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import re
from typing import Any, Mapping


_NUM = r"(?:\d+(?:\.\d+)?|\.\d+)"
_ALIASES = {
    "seed": "seed", "rng_seed": "seed", "random_seed": "seed",
    "draws": "draws", "n_draws": "draws", "bootstrap_draws": "draws",
    "permutation_draws": "draws", "shuffle_draws": "draws",
    "block_length": "block_length", "block_size": "block_length",
    "nw_lag": "nw_lag", "newey_west_lag": "nw_lag", "lag": "nw_lag",
    "horizon": "horizon", "horizons": "horizon", "holding_horizon": "horizon",
    "window": "window", "windows": "window", "event_windows": "window",
    "top_n": "top_n", "n_long": "top_n", "holdings": "top_n",
    "cost_per_side": "cost_per_side", "side_cost": "cost_per_side",
    "turnover_cap": "turnover_cap", "max_turnover": "turnover_cap",
    "trial_count": "trial_count", "trials": "trial_count",
    "min_event_dates": "min_event_dates", "minimum_event_dates": "min_event_dates",
    "min_recipients": "min_recipients", "minimum_recipients": "min_recipients",
    "min_pairs": "min_pairs", "minimum_pairs": "min_pairs",
    "min_ic": "min_ic", "minimum_ic": "min_ic", "ic_floor": "min_ic",
    "min_t": "min_t", "minimum_t": "min_t", "t_floor": "min_t",
    "active_share_min": "active_share_min", "min_active_share": "active_share_min",
    "response_shift_sessions": "response_shift_sessions", "shift_sessions": "response_shift_sessions",
    "endpoint_ids": "endpoint_ids", "endpoints": "endpoint_ids",
    "alpha": "alpha", "significance_level": "alpha",
    "significance_alpha": "alpha", "pvalue_alpha": "alpha",
    "percentile": "percentile", "placebo_percentile": "percentile",
    "confidence_level": "confidence_level", "ci_level": "confidence_level",
    "variant_count": "variant_count", "variants": "variant_count",
    "endpoint_count": "endpoint_count", "holm_family_count": "endpoint_count",
}


@dataclass(frozen=True)
class PreregDifference:
    key: str
    preregistered: tuple[float, ...]
    declared: tuple[float, ...] | None
    status: str


@dataclass(frozen=True)
class PreregDiffResult:
    facts: dict[str, tuple[float, ...]]
    differences: tuple[PreregDifference, ...]

    @property
    def matches(self) -> bool:
        return not self.differences

    def require_match(self) -> None:
        if self.differences:
            details = "; ".join(
                f"{d.key}: prereg={d.preregistered}, runner={d.declared} ({d.status})"
                for d in self.differences
            )
            raise ValueError("runner config does not match preregistration: " + details)


def _canonical_key(key: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
    return _ALIASES.get(normalized, normalized)


def _values(text: str) -> tuple[float, ...]:
    out = []
    for token in re.findall(_NUM, text):
        value = float(token)
        if value.is_integer():
            value = int(value)
        out.append(float(value))
    return tuple(out)


def _append(facts: dict[str, list[float]], key: str, values: tuple[float, ...], percent=False):
    if percent and key in {"cost_per_side", "turnover_cap", "active_share_min", "min_shuffle_coverage_pct"}:
        values = tuple(v / 100.0 for v in values)
    facts.setdefault(key, []).extend(values)


def extract_prereg_numbers(prereg: str | Path) -> dict[str, tuple[float, ...]]:
    """Extract numeric design facts from markdown text or a path.

    The parser skips freeze/hash lines and citations. It recognizes the design
    terms below, keeps multiple window/horizon values, and records endpoint
    identifiers from numbered lists under an Endpoint heading.
    """
    if isinstance(prereg, Path) or (isinstance(prereg, str) and "\n" not in prereg and Path(prereg).is_file()):
        text = Path(prereg).read_text(encoding="utf-8")
    else:
        text = str(prereg)
    facts: dict[str, list[float]] = {}
    in_endpoint_list = False
    for raw in text.splitlines():
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", raw).strip()
        if not line or re.match(r"^(FROZEN|SHA256):", line, re.I):
            continue
        if re.search(r"\b(?:doi|https?://|www\.)", line, re.I):
            continue
        if re.match(r"^#{1,6}\s+", line):
            in_endpoint_list = bool(re.search(r"endpoint", line, re.I))
        elif in_endpoint_list and re.match(r"^\s*(?:[-*]\s*)?\d+[.)]\s+", raw):
            m = re.match(r"^\s*(?:[-*]\s*)?(\d+)[.)]\s+", raw)
            if m:
                _append(facts, "endpoint_ids", (float(m.group(1)),))
        elif in_endpoint_list and raw.startswith("## "):
            in_endpoint_list = False

        # Capture every numeric value attached to a registered design label.
        patterns = [
            ("__assignment__", rf"\b([A-Za-z][A-Za-z0-9_]*)\s*=\s*({_NUM})\s*%?", False),
            ("seed", rf"\b(?:seed|random seed|rng seed)\s*(?:=|:|of)?\s*({_NUM})", False),
            ("draws", rf"\b({_NUM})\s*(?:placebo\s+|bootstrap\s+|shuffle\s+|permutation\s+)?draws?\b", False),
            ("block_length", rf"\b({_NUM})[- ](?:trading\s+)?(?:sessions?|days?|months?)\s+blocks?\b", False),
            ("block_length", rf"\bblock(?:\s+length)?\s*(?:of|=|:)?\s*({_NUM})\s*(?:[- ]?(?:trading\s+)?(?:sessions?|days?|months?))?", False),
            ("nw_lag", rf"\b(?:newey[- ]west|nw)(?:\s+bartlett)?\s+(?:lag\s*)({_NUM})|\blag\s*({_NUM})\s*(?:for|in)?\s*(?:the\s+)?newey[- ]west", False),
            ("horizon", rf"\b(?:primary\s+)?horizons?\s*(?:of|=|:|is)?\s*\[?((?:{_NUM}\s*[,/and-]?\s*)+)\]?|\b({_NUM})[- ](?:session|trading day|day|month)\s+horizon", False),
            ("window", rf"\bwindows?\s*(?:of|=|:)?\s*\[?((?:{_NUM}\s*[,/and-]?\s*)+)\]?", False),
            ("top_n", rf"\b(?:top|select|hold)\s+({_NUM})\s+(?:assets?|stocks?|names?|suppliers?|securities|etfs?)", False),
            ("cost_per_side", rf"\b({_NUM})\s*%\s*(?:per|/)\s*side\b", True),
            ("turnover_cap", rf"\b(?:turnover\s*(?:cap|limit)?\s*(?:of|=|:|is|at most|less than)?\s*|cap\s+(?:total\s+)?traded\s+notional\s+(?:at|to)\s+)({_NUM})\s*(?:nav|%|per rebalance)?", False),
            ("trial_count", rf"\b(?:trial_count|trial count|trials)\s*(?:=|:|of)?\s*({_NUM})|\bfull\s+trial\s+count\s*(?:of)?\s*({_NUM})", False),
            ("variant_count", rf"\b({_NUM})\s+(?:distinct\s+)?variants?\b", False),
            ("endpoint_count", rf"\b({_NUM})\s+(?:registered\s+|total\s+|inferential\s+)?endpoints?\b", False),
            ("percentile", rf"\b({_NUM})(?:st|nd|rd|th)\s+percentile\b", False),
            ("confidence_level", rf"\b({_NUM})\s*%\s+(?:confidence\s+interval|CI)\b", True),
            ("alpha", rf"\bp(?:-value)?(?:\s+threshold)?\s*(?:<|less than)\s*({_NUM})", False),
            ("min_event_dates", rf"\b(?:at least|minimum|min\.?|≥)\s*({_NUM})\s+(?:distinct\s+)?(?:event[- ]response\s+)?dates?\b", False),
            ("min_recipients", rf"\b(?:at least|minimum|min\.?|≥)\s*({_NUM})\s+(?:distinct\s+)?(?:active\s+)?(?:Dow\s+)?(?:supplier\s+)?recipients?\b", False),
            ("min_pairs", rf"\b(?:at least|minimum|min\.?|≥)\s*({_NUM})\s+(?:distinct\s+)?(?:directed\s+)?(?:Dow\s+)?(?:customer[- ]supplier\s+)?pairs?\b", False),
            ("min_ic", rf"\b(?:mean\s+IC|IC)\s*(?:≥|>=|>|of at least|at least)\s*({_NUM})", False),
            ("min_t", rf"\b(?:NW\s+)?t(?:[- ]stat(?:istic)?)?\s*(?:≥|>=|>|of at least|at least)\s*({_NUM})", False),
            ("active_share_min", rf"\bactive[- ]share\s*(?:of|is|≥|>=|at least)?\s*({_NUM})\s*%?", True),
            ("response_shift_sessions", rf"\b(?:shift|move)\s+(?:each\s+)?(?:actual\s+)?event[- ]response\s+date\s+(?:exactly\s+)?({_NUM})\s+trading\s+sessions?", False),
            ("min_shuffle_coverage_pct", rf"\b(?:100|[1-9]?\d(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:all\s+)?(?:event\s+)?dates?\b[^.\n]{0,100}\b(?:shuffle|permutation)\w*\s+(?:coverage|eligible|feasible)", True),
        ]
        for pattern_key, pattern, is_percent in patterns:
            for m in re.finditer(pattern, line, re.I):
                # Multiple windows in a bracket list live in one capture.
                raw_values = m.groups()
                if pattern_key == "__assignment__":
                    key = _canonical_key(raw_values[0])
                    val_text = raw_values[1]
                    vals = _values(val_text)
                    if vals:
                        _append(facts, key, vals, bool("%" in m.group(0) and key in {"cost_per_side", "turnover_cap", "active_share_min"}))
                    continue
                val_text = next((g for g in raw_values if g is not None), "")
                vals = _values(val_text)
                if vals:
                    _append(facts, pattern_key, vals, is_percent)

    if "endpoint_ids" in facts and "endpoint_count" not in facts:
        facts["endpoint_count"] = [float(len(set(facts["endpoint_ids"]))) ]

    # Stable unique values preserve prereg list order (essential for endpoint
    # IDs and windows), while repeated prose mentions do not create noise.
    return {k: tuple(dict.fromkeys(v)) for k, v in facts.items()}


def prereg_diff(prereg: str | Path, declared_config: Mapping[str, Any]) -> PreregDiffResult:
    """Compare extracted prereg facts with a runner's declared config.

    Every extracted key must be explicitly supplied. Scalar config values are
    promoted to one-element tuples; list/tuple values are kept in order.
    Percentage config values for costs and share thresholds should be passed
    as fractions (e.g. 0.0005 for 0.05%).
    """
    expected = extract_prereg_numbers(prereg)
    declared: dict[str, tuple[float, ...]] = {}
    for raw_key, raw_value in declared_config.items():
        key = _canonical_key(raw_key)
        if isinstance(raw_value, (list, tuple)):
            seq = raw_value
        elif isinstance(raw_value, str) and key in {"window", "horizon", "endpoint_ids"}:
            seq = re.findall(_NUM, raw_value)
        else:
            seq = (raw_value,)
        try:
            vals = tuple(float(x) for x in seq)
        except (TypeError, ValueError):
            continue
        if vals:
            declared[key] = tuple(dict.fromkeys(vals))

    differences = []
    for key, values in expected.items():
        actual = declared.get(key)
        if actual is None:
            differences.append(PreregDifference(key, values, None, "missing from runner config"))
        elif len(actual) != len(values) or any(abs(a-b) > 1e-12 for a, b in zip(actual, values)):
            differences.append(PreregDifference(key, values, actual, "value mismatch"))
    for key, values in declared.items():
        if key not in expected:
            differences.append(PreregDifference(key, (), values, "runner parameter is not registered in preregistration"))
    return PreregDiffResult(expected, tuple(differences))


def main(argv=None) -> int:
    """CLI: ``python -m r4_harness.prereg_diff PREREG.md RUNNER_CONFIG.json``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prereg", type=Path)
    parser.add_argument("runner_config", type=Path,
                        help="JSON object declaring the runner's numeric settings")
    args = parser.parse_args(argv)
    config = json.loads(args.runner_config.read_text(encoding="utf-8"))
    result = prereg_diff(args.prereg, config)
    print(json.dumps({"matches": result.matches,
                      "prereg_facts": result.facts,
                      "differences": [d.__dict__ for d in result.differences]}, indent=2))
    return 0 if result.matches else 1


if __name__ == "__main__":
    raise SystemExit(main())

