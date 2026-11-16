"""Fail-closed wrapper for a single frozen, explicitly authorized run."""
from __future__ import annotations

from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import date, datetime, timezone
from typing import Callable

from .phase3 import prereg_digest


def validate_frozen_prereg(path: str | Path) -> tuple[str, str]:
    """Return (freeze date, canonical digest), rejecting malformed/tampered files."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"pre-registration not found: {p}")
    text = p.read_text(encoding="utf-8")
    fm = re.search(r"^FROZEN:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M)
    hm = re.search(r"^SHA256:\s*([0-9a-fA-F]{64})\s*$", text, re.M)
    if not fm or not hm:
        raise ValueError("pre-registration requires FROZEN: YYYY-MM-DD and SHA256: <64 hex>")
    try:
        date.fromisoformat(fm.group(1))
    except ValueError as exc:
        raise ValueError("FROZEN date must be a valid calendar date") from exc
    actual = prereg_digest(text)
    if actual.lower() != hm.group(1).lower():
        raise ValueError("pre-registration content hash does not match SHA256 line")
    return fm.group(1), actual


def _mechanism_files(run_dir: Path) -> list[Path]:
    if not run_dir.is_dir():
        return []
    return sorted(p for p in run_dir.iterdir()
                  if p.is_file() and p.name.upper().startswith("MECHANISM_"))


def guarded_runner(*, prereg_path: str | Path | None = None,
                   run_dir: str | Path | None = None,
                   lock_name: str = ".runner.lock"):
    """Decorate a runner with freeze/hash, ``--execute``, lock and artifact gates.

    The decorated callable accepts optional keyword overrides ``prereg_path``,
    ``run_dir`` and ``execute``. In a CLI entry point the ``--execute`` token
    in ``sys.argv`` is also recognized. The lock is retained after completion
    or failure, so a run has one owner and must be reviewed before any retry.
    """
    def decorate(function: Callable):
        @wraps(function)
        def wrapped(*args, **kwargs):
            explicit = kwargs.pop("execute", None)
            if explicit is not True and "--execute" not in sys.argv:
                raise PermissionError("runner requires explicit --execute authorization")
            prereg_override = kwargs.pop("prereg_path", None)
            run_override = kwargs.pop("run_dir", None)
            if prereg_override is None and prereg_path is None:
                raise ValueError("guarded_runner needs prereg_path")
            if run_override is None and run_dir is None:
                raise ValueError("guarded_runner needs run_dir")
            p = Path(prereg_override if prereg_override is not None else prereg_path)
            out = Path(run_override if run_override is not None else run_dir)
            frozen_date, digest = validate_frozen_prereg(p)
            out.mkdir(parents=True, exist_ok=True)
            artifacts = _mechanism_files(out)
            if artifacts:
                raise FileExistsError("mechanism artifact already exists: " + ", ".join(x.name for x in artifacts))
            lock = out / lock_name
            payload = json.dumps({
                "pid": os.getpid(), "approach": p.stem,
                "frozen_date": frozen_date, "prereg_sha256": digest,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }, sort_keys=True) + "\n"
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                raise FileExistsError(f"run is already locked by {lock}") from exc
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                # Recheck under the lock to close the artifact race.
                artifacts = _mechanism_files(out)
                if artifacts:
                    raise FileExistsError("mechanism artifact already exists: " + ", ".join(x.name for x in artifacts))
                return function(*args, **kwargs)
            except BaseException:
                # Fail closed: retain the lock, even when the runner raises.
                raise
        return wrapped
    return decorate

