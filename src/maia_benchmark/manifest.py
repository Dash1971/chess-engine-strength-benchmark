from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from .books import validate_book
from .config import Experiment


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(
    exp: Experiment,
    openings_path: Path,
    results_dir: Path,
    engine_infos: list[dict],
    record_moves: bool,
) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "manifest.json"
    repo = exp.path.parent.parent
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    books = [validate_book(exp.book_path(rating)) for rating in exp.ratings]
    payload = {
        "manifest_schema": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "experiment_sha256": exp.digest(),
        "git_commit": commit,
        "openings_sha256": file_sha256(openings_path),
        "books": [
            {"rating": rating, "sha256": info.sha256, "entries": info.entries}
            for rating, info in zip(exp.ratings, books)
        ],
        "engines": [
            {key: value for key, value in info.items() if key not in {"probe_move", "probe_nodes"}}
            for info in engine_infos
        ],
        "dependencies": {"chess": version("chess")},
        "platform": platform.platform(),
        "python": platform.python_version(),
        "record_moves": record_moves,
    }
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        comparable_existing = existing | {"started_at": payload["started_at"]}
        if comparable_existing != payload:
            raise RuntimeError(f"Result directory already has a different manifest: {path}")
        return path
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(encoded, encoding="utf-8")
    return path
