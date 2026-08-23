from __future__ import annotations

import argparse
from pathlib import Path

from .match import EngineConfig, MatchConfig, MatchRunner


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="maia-benchmark",
        description="Play a color-balanced match between two installed UCI engines.",
    )
    _engine_arguments(p, "a", "Engine A")
    _engine_arguments(p, "b", "Engine B")
    p.add_argument("--number-of-games", type=int, required=True, help="Even number of games.")
    p.add_argument("--output", type=Path, default=Path("benchmark-games.pgn"))
    p.add_argument("--nodes", type=int, default=1, help="Nodes requested per engine move.")
    p.add_argument("--move-time-ms", type=int, help="Use a time limit instead of --nodes.")
    p.add_argument("--max-plies", type=int, default=300)
    p.add_argument("--seed", type=int, help="Optional seed for opening-book choices.")
    return p


def _engine_arguments(p: argparse.ArgumentParser, side: str, title: str) -> None:
    group = p.add_argument_group(title)
    prefix = f"--engine-{side}-"
    group.add_argument(f"{prefix}path", type=Path, required=True)
    group.add_argument(f"{prefix}name", default=title)
    group.add_argument(f"{prefix}elo", type=int)
    group.add_argument(f"{prefix}self-elo", type=int)
    group.add_argument(f"{prefix}opponent-elo", type=int)
    group.add_argument(f"{prefix}temperature", type=float)
    group.add_argument(f"{prefix}top-p", type=float)
    group.add_argument(f"{prefix}book", type=Path)


def _engine_config(args: argparse.Namespace, side: str) -> EngineConfig:
    key = f"engine_{side}_"
    return EngineConfig(
        label=getattr(args, f"{key}name"),
        path=getattr(args, f"{key}path").expanduser().resolve(),
        elo=getattr(args, f"{key}elo"),
        self_elo=getattr(args, f"{key}self_elo"),
        opponent_elo=getattr(args, f"{key}opponent_elo"),
        temperature=getattr(args, f"{key}temperature"),
        top_p=getattr(args, f"{key}top_p"),
        book=(
            getattr(args, f"{key}book").expanduser().resolve()
            if getattr(args, f"{key}book") is not None
            else None
        ),
    )


def main() -> None:
    args = parser().parse_args()
    config = MatchConfig(
        engine_a=_engine_config(args, "a"),
        engine_b=_engine_config(args, "b"),
        number_of_games=args.number_of_games,
        output=args.output.expanduser().resolve(),
        nodes=args.nodes,
        move_time_ms=args.move_time_ms,
        max_plies=args.max_plies,
        seed=args.seed,
    )
    try:
        summary = MatchRunner(config).run()
    except (OSError, ValueError, RuntimeError) as error:
        raise SystemExit(f"Error: {error}") from error
    print("\nMatch complete")
    print(f"Engine A: {config.engine_a.label}")
    print(f"Engine B: {config.engine_b.label}")
    print(
        f"Engine A result: {summary.engine_a_wins} wins / {summary.draws} draws / "
        f"{summary.engine_a_losses} losses"
    )
    print(f"Win percentage: {summary.win_percentage:.1f}%")
    print(f"Score percentage: {summary.score_percentage:.1f}%")
    print(f"Elapsed: {summary.elapsed_seconds:.1f} seconds")
    print(f"PGN: {summary.output}")


if __name__ == "__main__":
    main()
