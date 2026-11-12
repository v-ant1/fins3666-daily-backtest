"""Governance-first skeleton for future, frozen development runners.

This module does not know how to load project outcomes. Callers provide an
``analyze(governance)`` function, which is invoked only after preregistration,
input manifest/date bounds, Holm family, trial registry, paths, and the one-run
lock have passed. Existing runners are intentionally not changed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Callable, Mapping

from r4_harness.phase3 import append_trial, holm_correction
from r4_harness.runner_guard import guarded_runner, validate_frozen_prereg

DEVELOPMENT_START = "2020-11-27"
DEVELOPMENT_END = "2026-10-30"
TRIAL_BUDGET = 30
VARIANT_ID = re.compile(r"\b([A-Z]\d+-V1)\b")


class GovernanceError(RuntimeError):
    """An input or registry failed the pre-analysis governance gates."""


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value).encode("utf-8")).hexdigest()


def validate_input_manifest(path: str | Path, *, project_root: str | Path,
                            expected_window: tuple[str, str] = (DEVELOPMENT_START, DEVELOPMENT_END)) -> dict:
    """Hash-check a worker's inputs and enforce development-only date bounds.

    Expected schema: ``RUNNER_INPUTS_V1``, ``development_window`` (two ISO
    dates), ``input_date_min``, ``input_date_max``, ``holdout_loaded: false``,
    and ``files`` as a list of ``{path, sha256}`` records. The date metadata is
    a provenance attestation from the input builder; this check also verifies
    every referenced file's bytes and rejects paths whose names indicate a
    pre-window file or a sealed holdout folder.
    """
    p = Path(path).resolve()
    root = Path(project_root).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"input manifest not found: {p}")
    obj = json.loads(p.read_text(encoding="utf-8"))
    if obj.get("schema") != "RUNNER_INPUTS_V1":
        raise GovernanceError("input manifest schema must be RUNNER_INPUTS_V1")
    window = obj.get("development_window")
    if window != list(expected_window):
        raise GovernanceError("input manifest development_window differs from the registered window")
    if obj.get("holdout_loaded") is not False:
        raise GovernanceError("worker input manifest must attest holdout_loaded=false")
    try:
        min_date = date.fromisoformat(str(obj["input_date_min"]))
        max_date = date.fromisoformat(str(obj["input_date_max"]))
        permitted_min = date.fromisoformat(expected_window[0])
        permitted_max = date.fromisoformat(expected_window[1])
    except (KeyError, ValueError) as exc:
        raise GovernanceError("manifest must contain ISO input_date_min and input_date_max") from exc
    if min_date < permitted_min:
        raise GovernanceError(f"worker input starts before {expected_window[0]}")
    if max_date > permitted_max or max_date < min_date:
        raise GovernanceError("worker input date bounds exceed or reverse the development window")
    entries = obj.get("files")
    if not isinstance(entries, list) or not entries:
        raise GovernanceError("manifest files must be a nonempty list")
    seen: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not {"path", "sha256"}.issubset(entry):
            raise GovernanceError("each manifest file requires path and sha256")
        input_path = (root / str(entry["path"])).resolve()
        if root not in input_path.parents:
            raise GovernanceError(f"input path escapes project root: {entry['path']}")
        if any(part.casefold() in {"holdout", "sealed_holdout", "sealed-holdout"}
               for part in input_path.parts):
            raise GovernanceError(f"worker path may not reference holdout data: {entry['path']}")
        if input_path in seen:
            raise GovernanceError(f"duplicate manifest path: {entry['path']}")
        seen.add(input_path)
        # Catch date-stamped names in any directory component as an additional
        # guard: nothing on a worker input path may name data before the
        # 2020-11-27 development start.
        for component in input_path.parts:
            for match in re.finditer(r"(?<!\d)(\d{4})[-_]?([01]\d)[-_]?([0-3]\d)(?!\d)", component):
                try:
                    named_date = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except ValueError:
                    continue
                if named_date < permitted_min:
                    raise GovernanceError(f"worker path names pre-window data: {entry['path']}")
        if not input_path.is_file():
            raise FileNotFoundError(f"manifest input missing: {entry['path']}")
        if sha256_file(input_path).lower() != str(entry["sha256"]).lower():
            raise GovernanceError(f"input SHA-256 mismatch: {entry['path']}")
    return obj


def read_holm_family(path: str | Path, current_p_values: Mapping[str, float | None] | None = None) -> dict:
    """Validate the R6 manifest and return Holm results, preserving unrun nulls.

    The coordinator convention hashes ``sha256(json.dumps(manifest))`` with
    Python's default separators. Null p-value slots remain null in
    ``raw_p_values`` and are mapped to 1.0 only for Holm correction.
    """
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest, prior = obj.get("manifest"), obj.get("p_values")
    if (not isinstance(manifest, list) or not manifest or
            any(not isinstance(x, str) for x in manifest) or len(set(manifest)) != len(manifest)):
        raise GovernanceError("Holm manifest must be a nonempty list of unique endpoint IDs")
    if _sha256_json(manifest) != obj.get("manifest_sha256"):
        raise GovernanceError("Holm manifest/hash mismatch")
    if not isinstance(prior, dict) or set(prior) != set(manifest):
        raise GovernanceError("Holm p_values must include every manifest endpoint")
    current = dict(current_p_values or {})
    if not set(current).issubset(manifest):
        raise GovernanceError("current p-values include endpoints outside the frozen Holm family")
    raw: dict[str, float | None] = {}
    correction: dict[str, float] = {}
    for endpoint in manifest:
        value = current.get(endpoint, prior[endpoint])
        if value is not None:
            value = float(value)
            if not 0 <= value <= 1:
                raise GovernanceError(f"invalid p-value for {endpoint}")
        raw[endpoint] = value
        correction[endpoint] = 1.0 if value is None else value
    return {"manifest": manifest, "raw_p_values": raw,
            "holm": holm_correction(correction),
            "status": {key: ("not run" if raw[key] is None else "computed") for key in manifest}}


def count_cumulative_r6_variants(trial_log: str | Path, *, limit: int = TRIAL_BUDGET) -> int:
    """Count unique R6 variant IDs in the R6 registry, not trial-table rows."""
    text = Path(trial_log).read_text(encoding="utf-8")
    marker = "## R6 Holm family"
    if marker not in text:
        raise GovernanceError("trial log lacks the R6 variant registry section")
    ids = set(VARIANT_ID.findall(text.split(marker, 1)[1]))
    if not ids:
        raise GovernanceError("R6 variant registry is empty")
    if len(ids) > limit:
        raise GovernanceError(f"R6 registry exceeds the {limit}-variant budget")
    return len(ids)


def governance_preflight(*, approach: str, variant: str, prereg_path: str | Path,
                         expected_prereg_sha256: str, prereg_dir: str | Path,
                         input_manifest_path: str | Path, holm_path: str | Path,
                         trial_log: str | Path, project_root: str | Path,
                         expected_window: tuple[str, str] = (DEVELOPMENT_START, DEVELOPMENT_END)) -> dict:
    """Complete all non-outcome checks before caller analysis is allowed."""
    prereg = Path(prereg_path).resolve()
    folder = Path(prereg_dir).resolve()
    if prereg.parent != folder:
        raise GovernanceError("pre-registration must be in the explicit specs/r6_prereg directory")
    _, digest = validate_frozen_prereg(prereg)
    if digest.lower() != expected_prereg_sha256.lower():
        raise GovernanceError("frozen preregistration differs from its reviewed SHA-256")
    manifest = validate_input_manifest(input_manifest_path, project_root=project_root,
                                       expected_window=expected_window)
    holm = read_holm_family(holm_path)
    variants = count_cumulative_r6_variants(trial_log)
    if not VARIANT_ID.fullmatch(variant) or variant not in set(VARIANT_ID.findall(
            Path(trial_log).read_text(encoding="utf-8").split("## R6 Holm family", 1)[1])):
        raise GovernanceError(f"{variant} is not registered in the R6 variant registry")
    if not re.fullmatch(r"[A-Z][A-Z0-9_-]*", approach):
        raise GovernanceError("approach must be a safe uppercase identifier")
    return {"approach": approach, "variant": variant, "prereg_sha256": digest,
            "input_manifest_sha256": sha256_file(input_manifest_path),
            "input_manifest": manifest, "holm": holm, "trial_count": variants,
            "expected_window": list(expected_window)}


def _json_safe(value):
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot JSON-serialize {type(value).__name__}")


def write_result_atomic(path: str | Path, result: Mapping) -> Path:
    """Write a complete JSON result through a same-directory atomic replace."""
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"immutable result path already exists: {target}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, indent=2, allow_nan=False, default=_json_safe)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if target.exists():
            raise FileExistsError(f"immutable result path appeared during write: {target}")
        # A same-directory hard link is atomic and fails if another writer has
        # claimed the immutable destination; unlike replace(), it cannot clobber.
        os.link(temp_name, target)
        os.unlink(temp_name)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return target


def run_template(*, approach: str, variant: str, prereg_path: str | Path,
                 expected_prereg_sha256: str, prereg_dir: str | Path,
                 input_manifest_path: str | Path, holm_path: str | Path,
                 trial_log: str | Path, project_root: str | Path,
                 run_dir: str | Path, result_path: str | Path,
                 analyze: Callable[[dict], Mapping], execute: bool = False,
                 expected_window: tuple[str, str] = (DEVELOPMENT_START, DEVELOPMENT_END),
                 trial_date: str | None = None) -> dict:
    """Guard, preflight, analyze, atomically persist, then append the trial."""
    result_file = Path(result_path).resolve()
    run_folder = Path(run_dir).resolve()
    if result_file.exists():
        raise FileExistsError(f"immutable result path already exists: {result_file}")
    if run_folder in result_file.parents or result_file == run_folder:
        raise GovernanceError("result file must be separate from the one-shot lock directory")

    # Fail closed before acquiring the run lock if any registry or manifest
    # check is bad. No outcome arrays are loaded by this shared skeleton.
    if execute is not True and "--execute" not in sys.argv:
        raise PermissionError("runner requires explicit --execute authorization")
    governance_preflight(
        approach=approach, variant=variant, prereg_path=prereg_path,
        expected_prereg_sha256=expected_prereg_sha256, prereg_dir=prereg_dir,
        input_manifest_path=input_manifest_path, holm_path=holm_path,
        trial_log=trial_log, project_root=project_root, expected_window=expected_window)

    @guarded_runner(prereg_path=prereg_path, run_dir=run_dir)
    def _guarded_execute():
        # Recheck under the one-shot lock to catch governance-file changes
        # between the preliminary preflight and lock acquisition.
        gov = governance_preflight(
            approach=approach, variant=variant, prereg_path=prereg_path,
            expected_prereg_sha256=expected_prereg_sha256, prereg_dir=prereg_dir,
            input_manifest_path=input_manifest_path, holm_path=holm_path,
            trial_log=trial_log, project_root=project_root, expected_window=expected_window)
        result = dict(analyze(gov))
        current = result.get("current_p_values", {})
        if not isinstance(current, dict):
            raise GovernanceError("analyze must return current_p_values as a mapping")
        updated_holm = read_holm_family(holm_path, current)
        result.update({
            "approach": approach,
            "variant": variant,
            "prereg_sha256": gov["prereg_sha256"],
            "input_manifest_sha256": gov["input_manifest_sha256"],
            "trial_count": gov["trial_count"],
            "holm": updated_holm,
        })
        saved = write_result_atomic(result_file, result)
        summary = f"{approach} {variant}: result={saved}; trial_count={gov['trial_count']}"
        append_trial(approach, variant, summary, prereg_dir=prereg_dir,
                     trial_log=trial_log, trial_date=trial_date)
        print(summary)
        return result

    return _guarded_execute(execute=execute, prereg_path=prereg_path, run_dir=run_dir)
