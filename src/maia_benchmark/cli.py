from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path

from .books import validate_book
from .config import load_experiment, profiles
from .openings import generate_openings, load_openings
from .report import build_report
from .runner import run_matchup
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
        exp.command("maia2")
        exp.command("maia3")
        print(json.dumps({"profiles": len(all_profiles), "matchups": len(all_matchups),
                          "games": len(all_matchups) * exp.games_per_matchup,
                          "books": [info.__dict__ | {"path": str(info.path)} for info in infos]},
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
        if args.workers == 1:
            for matchup in selected:
                print(run_matchup(exp, matchup, opening_rows, Path(args.results)))
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = [
                    pool.submit(run_matchup, exp, matchup, opening_rows, Path(args.results))
                    for matchup in selected
                ]
                for future in concurrent.futures.as_completed(futures):
                    print(future.result())
    elif args.command == "report":
        print(build_report(Path(args.results), Path(args.output)))


if __name__ == "__main__":
    main()
