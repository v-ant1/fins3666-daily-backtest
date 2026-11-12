"""Pre-run checks shared by D4/D5 portfolio and coordinator runners."""
from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from r4_harness.phase3 import prereg_digest, require_frozen_prereg


def trial_budget(trial_log: Path) -> int:
    text = Path(trial_log).read_text(encoding='utf-8')
    match = re.search(r'\bbudget\s*:\s*(\d+)\s+variants\b', text, re.I)
    if not match:
        raise ValueError('trial log must declare a variant budget in its heading')
    return int(match.group(1))


def require_mechanism_pass(approach: str, prereg_path: Path,
                          mechanism_pass_path: Path) -> dict:
    prereg_path = Path(prereg_path)
    frozen = require_frozen_prereg(approach, prereg_dir=prereg_path.parent)
    if frozen.resolve() != prereg_path.resolve():
        raise ValueError(f'expected frozen pre-registration at {frozen}')
    fail_path = Path(mechanism_pass_path).with_name('MECHANISM_FAIL.json')
    if fail_path.is_file():
        raise PermissionError(f'{approach} mechanism gate failed; portfolio and holdout are prohibited ({fail_path})')
    if not Path(mechanism_pass_path).is_file():
        raise PermissionError(f'{approach} portfolio is gated: missing {mechanism_pass_path}')
    proof = json.loads(Path(mechanism_pass_path).read_text(encoding='utf-8'))
    if proof.get('approach') != approach or proof.get('passed') is not True:
        raise PermissionError('mechanism-pass artifact does not certify a passing mechanism gate')
    expected = prereg_digest(frozen.read_text(encoding='utf-8'))
    if proof.get('prereg_sha256') != expected:
        raise PermissionError('mechanism-pass artifact was produced for a different frozen pre-registration')
    try:
        mean_ic = float(proof['mean_ic'])
        nw_t = float(proof['nw_t_lag4'])
    except (KeyError, TypeError, ValueError) as exc:
        raise PermissionError('mechanism-pass artifact must include primary mean IC and lag-4 NW t') from exc
    if mean_ic < .0183 or nw_t < 2.0:
        raise PermissionError('primary mechanism did not meet the pre-registered 0.0183 IC and NW t>=2 hurdle')
    return proof


def load_holm_family(path: Path, current_endpoint: str) -> dict[str, float]:
    """Load frozen round-wide raw p-values excluding this portfolio endpoint.

    Required JSON schema: ``{"manifest": [endpoint names],
    "manifest_sha256": <64 hex>, "p_values": {name: p}}``.
    The coordinator supplies this after the complete D4-D6 manifest and all
    other registered tests are fixed; ``current_endpoint`` is inserted by the
    runner before Holm adjustment.
    """
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    digest = str(obj.get('manifest_sha256', ''))
    if not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
        raise ValueError('Holm family must include the frozen manifest SHA-256')
    values = obj.get('p_values')
    if not isinstance(values, dict) or not values:
        raise ValueError('Holm family must contain raw p_values for every other endpoint')
    manifest = obj.get('manifest')
    if not isinstance(manifest, list) or not manifest or any(not isinstance(x, str) for x in manifest):
        raise ValueError('Holm family must contain the complete frozen endpoint-name manifest')
    if len(manifest) != len(set(manifest)) or current_endpoint not in manifest:
        raise ValueError(f'Holm endpoint manifest must be unique and include {current_endpoint}')
    actual_digest = hashlib.sha256(('\n'.join(manifest) + '\n').encode('utf-8')).hexdigest()
    if actual_digest.lower() != digest.lower():
        raise ValueError('Holm endpoint manifest SHA-256 does not match its contents')
    out = {}
    for key, value in values.items():
        if key == current_endpoint:
            raise ValueError('do not pre-fill the portfolio endpoint; the runner calculates it')
        number = float(value)
        if not (0.0 <= number <= 1.0):
            raise ValueError(f'invalid p-value for {key}')
        out[str(key)] = number
    expected_other = set(manifest) - {current_endpoint}
    if set(out) != expected_other:
        raise ValueError('Holm p-values must cover every manifest endpoint except the portfolio p calculated by this runner')
    return out
