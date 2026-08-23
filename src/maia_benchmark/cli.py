from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
from pathlib import Path

from .books import validate_book
from .config import load_experiment, profiles
from .manifest import write_manifest
from .openings import generate_openings, load_openings
from .report import build_report
from .runner import run_matchup, validate_engine
from .schedule import matchups


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="maia-benchmark")
    p.add_argument("--config", default="config/experiment.toml")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    openings = sub.add_parser("build-openings")
    openings.add_argument("--output", default="artifacts/openings.jsonl")
    schedule = sub.add_parser("schedule")
    schedule.add_argument("--output", default="artifacts/schedule.json")
    run = sub.add_parser("run")
    run.add_argument("--openings", default="artifacts/openings.jsonl")
    run.add_argument("--results", default="results/raw")
    run.add_argument("--matchup")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--record-moves", action="store_true")
    pilot = sub.add_parser("pilot")
    pilot.add_argument("--openings", default="artifacts/openings.jsonl")
    pilot.add_argument("--results", default="results/pilot")
    pilot.add_argument("--pairs", type=int, default=10)
    pilot.add_argument("--worker-counts", type=int, nargs="+", default=[1, 2, 4])
    report = sub.add_parser("report")
    report.add_argument("--results", default="results/raw")
    report.add_argument("--output", default="results/report")
    return p


def main() -> None:
    args = parser().parse_args()
    exp = load_experiment(args.config)
    all_profiles = profiles(exp)
    all_matchups = matchups(all_profiles)
    if args.command == "validate":
        infos = [validate_book(exp.book_path(rating)) for rating in exp.ratings]
        engine_infos = _validate_engines(exp, all_profiles)
        print(json.dumps({"profiles": len(all_profiles), "matchups": len(all_matchups),
                          "games": len(all_matchups) * exp.games_per_matchup,
                          "books": [info.__dict__ | {"path": str(info.path)} for info in infos],
                          "engines": engine_infos},
                         default=str, indent=2))
    elif args.command == "build-openings":
        print(f"Wrote {len(generate_openings(exp, Path(args.output)))} openings")
    elif args.command == "schedule":
        rows = [{"id": m.id, "a": m.a.id, "b": m.b.id,
                 "games": exp.games_per_matchup} for m in all_matchups]
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(rows)} matchups / {len(rows) * exp.games_per_matchup} games")
    elif args.command == "run":
        if args.workers < 1:
            raise SystemExit("--workers must be at least 1")
        selected = [m for m in all_matchups if not args.matchup or m.id == args.matchup]
        if args.matchup and not selected:
            raise SystemExit(f"Unknown matchup: {args.matchup}")
        opening_rows = load_openings(Path(args.openings))
        expected = exp.games_per_matchup // 2
        if exp.games_per_matchup % 2 or len(opening_rows) != expected:
            raise SystemExit(
                f"Expected {expected} opening positions for "
                f"{exp.games_per_matchup} color-balanced games; got {len(opening_rows)}"
            )
        results = Path(args.results)
        engine_infos = _validate_engines(exp, all_profiles)
        print(write_manifest(exp, Path(args.openings), results, engine_infos, args.record_moves))
        failures = _run_many(
            exp, selected, opening_rows, results, args.workers, args.record_moves
        )
        if failures:
            raise SystemExit(f"{len(failures)} matchups failed; see errors above")
    elif args.command == "pilot":
        if args.pairs < 1 or any(value < 1 for value in args.worker_counts):
            raise SystemExit("Pilot pairs and worker counts must be positive")
        opening_rows = load_openings(Path(args.openings))[:args.pairs]
        engine_infos = _validate_engines(exp, all_profiles)
        summaries = []
        for record_moves in (False, True):
            mode = "moves" if record_moves else "compact"
            for workers in args.worker_counts:
                selected = all_matchups[:workers]
                results = Path(args.results) / mode / f"workers-{workers}"
                write_manifest(exp, Path(args.openings), results, engine_infos, record_moves)
                started = time.perf_counter()
                failures = _run_many(
                    exp, selected, opening_rows, results, workers, record_moves
                )
                elapsed = time.perf_counter() - started
                games = len(selected) * len(opening_rows) * 2
                summary = {
                    "mode": mode, "workers": workers, "games": games,
                    "elapsed_seconds": elapsed, "games_per_hour": games / elapsed * 3600,
                    "failures": len(failures),
                }
                summaries.append(summary)
                print(json.dumps(summary, sort_keys=True))
        output = Path(args.results) / "pilot-summary.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    elif args.command == "report":
        print(build_report(Path(args.results), Path(args.output)))


def _validate_engines(exp, all_profiles) -> list[dict]:
    maia2 = next(profile for profile in all_profiles if profile.family == "maia2")
    maia3 = next(
        profile for profile in all_profiles
        if profile.family == "maia3" and profile.sampling.name == "argmax"
    )
    return [validate_engine(exp, maia2), validate_engine(exp, maia3)]


def _run_many(exp, selected, openings, results, workers, record_moves) -> list[str]:
    failures: list[str] = []
    if workers == 1:
        for matchup in selected:
            try:
                print(run_matchup(exp, matchup, openings, results, record_moves))
            except Exception as error:  # noqa: BLE001 - isolate a failed matchup
                failures.append(matchup.id)
                print(f"FAILED {matchup.id}: {type(error).__name__}: {error}")
        return failures
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(run_matchup, exp, matchup, openings, results, record_moves): matchup
            for matchup in selected
        }
        for future in concurrent.futures.as_completed(futures):
            matchup = futures[future]
            try:
                print(future.result())
            except Exception as error:  # noqa: BLE001 - isolate a failed worker
                failures.append(matchup.id)
                print(f"FAILED {matchup.id}: {type(error).__name__}: {error}")
    return failures


if __name__ == "__main__":
    main()
