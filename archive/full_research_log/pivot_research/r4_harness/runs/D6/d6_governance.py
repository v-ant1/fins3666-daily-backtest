"""D6-only freeze and mechanism-pass gates; validates before inputs are opened."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from r4_harness.phase3 import prereg_digest, require_frozen_prereg

PREREG = ROOT / 'specs' / 'r4_prereg' / 'D6.md'


def require_d6_frozen(prereg_path=PREREG):
    p = Path(prereg_path)
    checked = require_frozen_prereg('D6', p.parent)
    if checked.resolve() != p.resolve():
        raise ValueError(f'expected D6 preregistration at {p}')
    return checked


def require_d6_mechanism_pass(prereg_path=PREREG, pass_path=None):
    p = require_d6_frozen(prereg_path)
    proof_path = Path(pass_path) if pass_path else p.parent.parent.parent / 'r4_harness' / 'runs' / 'D6' / 'MECHANISM_PASS.json'
    fail_path = proof_path.with_name('MECHANISM_FAIL.json')
    if fail_path.exists():
        raise PermissionError(f'D6 mechanism gate failed; portfolio is prohibited ({fail_path})')
    if not proof_path.is_file():
        raise PermissionError(f'D6 portfolio is gated: missing {proof_path}')
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    if proof.get('approach') != 'D6' or proof.get('passed') is not True:
        raise PermissionError('D6 mechanism artifact does not certify a passing primary gate')
    if proof.get('prereg_sha256') != prereg_digest(p.read_text(encoding='utf-8')):
        raise PermissionError('D6 mechanism artifact was produced for a different frozen pre-registration')
    try:
        primary = proof.get('primary', {})
        primary_beta = float(proof.get('primary_beta', primary.get('beta')))
        primary_t = float(proof.get('nw_t_lag11', primary.get('nw_t_lag11')))
        placebo = proof.get('placebo', {})
        placebo_p = float(proof.get('placebo_p_one_sided', placebo.get('one_sided_randomization_p')))
        observed_above = proof.get('observed_above_placebo_p95',
            proof.get('gate', {}).get('observed_beta_exceeds_placebo_p95'))
        if primary_beta <= 0 or primary_t < 2:
            raise PermissionError('D6 primary mechanism artifact fails the registered sign/t gate')
        if placebo_p >= .05 or observed_above is not True:
            raise PermissionError('D6 mechanism artifact fails the registered circular-shift placebo gate')
    except (KeyError, TypeError, ValueError) as exc:
        raise PermissionError('D6 mechanism artifact is missing gate evidence') from exc
    return proof
