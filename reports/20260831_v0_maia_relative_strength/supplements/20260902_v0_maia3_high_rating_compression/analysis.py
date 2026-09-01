#!/usr/bin/env python3
"""Validate and analyze the frozen Maia 3 high-rating compression study."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import chess.pgn
import numpy as np
from scipy.optimize import minimize


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "data"
RUN_DIR = HERE / "data"
SUITE = HERE.parents[3] / "openings" / "maia-relative-strength-100.pgn"
EXPECTED_SUITE_HASH = "3ad5d17fcd30bac36ef7277b15232e7df27bdb0728faa9ab441503d826cbc171"
EXPECTED_SUITE_NAME = "maia-relative-strength-100.pgn"
MATCHUPS = ((1600, 2100), (1600, 2300))
BOOTSTRAPS = 20_000
PERMUTATIONS = 100_000
SEED = 20260901
ELO_SCALE = 400.0 / math.log(10.0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q, method="linear"))


def logistic_elo(score: float) -> float:
    if not 0.0 < score < 1.0:
        return math.copysign(math.inf, score - 0.5)
    return 400.0 * math.log10(score / (1.0 - score))


def score_for(result: str, is_white: bool) -> float:
    if result == "1/2-1/2":
        return 0.5
    return 1.0 if (result == "1-0") == is_white else 0.0


def load_opening_suite() -> dict[int, list[str]]:
    if sha256(SUITE) != EXPECTED_SUITE_HASH:
        raise ValueError("Frozen opening-suite SHA-256 mismatch")
    openings: dict[int, list[str]] = {}
    with SUITE.open(encoding="utf-8") as handle:
        while game := chess.pgn.read_game(handle):
            index = int(game.headers["Round"])
            if index in openings:
                raise ValueError(f"Duplicate opening-suite round {index}")
            openings[index] = [move.uci() for move in game.mainline_moves()]
    if set(openings) != set(range(1, 101)):
        raise ValueError("Opening-suite rounds are not exactly 1..100")
    if any(not moves for moves in openings.values()):
        raise ValueError("Opening suite contains an empty prefix")
    return openings


def load_match(low: int, high: int, openings: dict[int, list[str]]) -> dict:
    stem = f"maia3-{low}__vs__maia3-{high}"
    path = RUN_DIR / f"{stem}.pgn"
    low_name, high_name = f"MAIA3 {low}", f"MAIA3 {high}"
    expected_ratings = {low_name: str(low), high_name: str(high)}
    games = []
    with path.open(encoding="utf-8") as handle:
        while game := chess.pgn.read_game(handle):
            headers = game.headers
            result = headers.get("Result")
            if result not in {"1-0", "0-1", "1/2-1/2"}:
                raise ValueError(f"{path.name}: unresolved result {result!r}")
            white, black = headers.get("White"), headers.get("Black")
            if {white, black} != {low_name, high_name}:
                raise ValueError(f"{path.name}: unexpected players {white!r}, {black!r}")
            if headers.get("WhiteElo") != expected_ratings[white]:
                raise ValueError(f"{path.name}: WhiteElo does not match player label")
            if headers.get("BlackElo") != expected_ratings[black]:
                raise ValueError(f"{path.name}: BlackElo does not match player label")
            if headers.get("OpeningSuite") != EXPECTED_SUITE_NAME:
                raise ValueError(f"{path.name}: unexpected OpeningSuite header")
            opening_index = int(headers["OpeningIndex"])
            moves = [move.uci() for move in game.mainline_moves()]
            prefix = openings.get(opening_index)
            if prefix is None or moves[: len(prefix)] != prefix:
                raise ValueError(
                    f"{path.name}: game {headers.get('Round')} does not match frozen opening "
                    f"prefix {opening_index}"
                )
            plies = len(moves)
            termination = headers.get("Termination", "unknown")
            if plies >= 300 or "max" in termination.lower() or "limit" in termination.lower():
                raise ValueError(f"{path.name}: 300-ply cutoff in round {headers.get('Round')}")
            low_is_white = white == low_name
            games.append(
                {
                    "matchup": stem,
                    "round": int(headers["Round"]),
                    "opening_index": opening_index,
                    "low_player": low_name,
                    "high_player": high_name,
                    "low_rating": low,
                    "high_rating": high,
                    "low_color": "White" if low_is_white else "Black",
                    "white": white,
                    "black": black,
                    "white_elo": headers.get("WhiteElo"),
                    "black_elo": headers.get("BlackElo"),
                    "result": result,
                    "low_score": score_for(result, low_is_white),
                    "termination": termination,
                    "plies": plies,
                    "full_moves": math.ceil(plies / 2),
                    "config_hash": headers.get("ConfigHash", ""),
                    "opening_suite": headers.get("OpeningSuite", ""),
                    "source_pgn": path.name,
                }
            )
    if len(games) != 200:
        raise ValueError(f"{path.name}: expected 200 games, found {len(games)}")
    if [g["round"] for g in games] != list(range(1, 201)):
        raise ValueError(f"{path.name}: rounds are not exactly 1..200 in order")
    by_opening: dict[int, list[dict]] = defaultdict(list)
    for game in games:
        by_opening[game["opening_index"]].append(game)
    if set(by_opening) != set(range(1, 101)):
        raise ValueError(f"{path.name}: OpeningIndex values are not exactly 1..100")
    for opening_index, pair in by_opening.items():
        if len(pair) != 2:
            raise ValueError(f"{path.name}: opening {opening_index} does not occur twice")
        if {g["low_color"] for g in pair} != {"White", "Black"}:
            raise ValueError(f"{path.name}: opening {opening_index} is not color reversed")
    config_hashes = {g["config_hash"] for g in games}
    if len(config_hashes) != 1 or not next(iter(config_hashes)):
        raise ValueError(f"{path.name}: expected one nonempty ConfigHash")
    clusters = np.array(
        [[g["low_score"] for g in sorted(by_opening[i], key=lambda item: item["round"])] for i in range(1, 101)],
        dtype=float,
    )
    return {
        "path": path,
        "stem": stem,
        "low": low,
        "high": high,
        "games": games,
        "clusters": clusters,
        "config_hash": next(iter(config_hashes)),
    }


def bootstrap_scores(clusters: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    indices = rng.integers(0, len(clusters), size=(BOOTSTRAPS, len(clusters)))
    return clusters.sum(axis=1)[indices].mean(axis=1) / 2.0


def sign_flip_p(clusters: np.ndarray, rng: np.random.Generator) -> float:
    deviations = clusters.sum(axis=1) - 1.0
    observed = abs(float(deviations.sum()))
    extreme = 0
    done = 0
    while done < PERMUTATIONS:
        batch = min(5_000, PERMUTATIONS - done)
        signs = rng.integers(0, 2, size=(batch, len(deviations)), dtype=np.int8) * 2 - 1
        extreme += int(np.count_nonzero(np.abs(signs @ deviations) >= observed - 1e-12))
        done += batch
    return (extreme + 1.0) / (PERMUTATIONS + 1.0)


def holm(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def bt_strengths(matches: list[dict], scores: list[float] | None = None) -> np.ndarray:
    if scores is None:
        scores = [float(match["clusters"].mean()) for match in matches]
    strengths = [0.0]
    for score in scores:
        clipped = min(max(1.0 - score, 1e-12), 1.0 - 1e-12)
        strengths.append(logistic_elo(clipped))
    return np.array(strengths)


def slope(strengths: np.ndarray) -> float:
    return float(np.polyfit(np.array([1600.0, 2100.0, 2300.0]), strengths, 1)[0])


def fit_davidson(matches: list[dict]) -> dict:
    edges = []
    for j, match in enumerate(matches, start=1):
        scores = np.array([game["low_score"] for game in match["games"]])
        edges.append(
            {
                "i": 0,
                "j": j,
                "wins": int(np.count_nonzero(scores == 1.0)),
                "draws": int(np.count_nonzero(scores == 0.5)),
                "losses": int(np.count_nonzero(scores == 0.0)),
            }
        )

    def objective(params: np.ndarray) -> float:
        x = np.r_[0.0, params[:2]]
        nu = math.exp(float(params[2]))
        log_likelihood = 0.0
        for edge in edges:
            ai, aj = math.exp(x[edge["i"]]), math.exp(x[edge["j"]])
            draw_weight = nu * math.sqrt(ai * aj)
            total = ai + aj + draw_weight
            log_likelihood += edge["wins"] * math.log(ai / total)
            log_likelihood += edge["losses"] * math.log(aj / total)
            log_likelihood += edge["draws"] * math.log(draw_weight / total)
        return -log_likelihood

    initial_bt = bt_strengths(matches)[1:] / ELO_SCALE
    initial_draw_rate = sum(edge["draws"] for edge in edges) / 400.0
    initial_nu = max(initial_draw_rate / max(1.0 - initial_draw_rate, 1e-9), 1e-6) * 2.0
    initial = np.r_[initial_bt, math.log(initial_nu)]
    result = minimize(objective, initial, method="BFGS", options={"gtol": 1e-10, "maxiter": 2_000})
    gradient_norm = float(np.linalg.norm(result.jac))
    stable = bool(np.all(np.isfinite(result.x)) and gradient_norm <= 5e-5)
    if not stable:
        return {
            "stable": False,
            "message": result.message,
            "gradient_norm": gradient_norm,
        }
    strengths = np.r_[0.0, result.x[:2]] * ELO_SCALE
    nu = math.exp(float(result.x[2]))
    fitted = []
    for edge in edges:
        x = strengths / ELO_SCALE
        ai, aj = math.exp(x[edge["i"]]), math.exp(x[edge["j"]])
        draw_weight = nu * math.sqrt(ai * aj)
        total = ai + aj + draw_weight
        fitted.append(
            {
                "matchup": matches[edge["j"] - 1]["stem"],
                "low_win_probability": ai / total,
                "draw_probability": draw_weight / total,
                "high_win_probability": aj / total,
            }
        )
    return {
        "stable": True,
        "optimizer_message": result.message,
        "gradient_norm": gradient_norm,
        "negative_log_likelihood": float(result.fun),
        "draw_nu": nu,
        "relative_elo": {"1600": float(strengths[0]), "2100": float(strengths[1]), "2300": float(strengths[2])},
        "strength_on_label_slope": slope(strengths),
        "fitted_probabilities": fitted,
    }


def write_csv(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    expected_names = {f"maia3-{low}__vs__maia3-{high}.pgn" for low, high in MATCHUPS}
    actual_names = {path.name for path in RUN_DIR.glob("*.pgn")}
    if actual_names != expected_names:
        raise ValueError(f"Expected exactly PGNs {sorted(expected_names)}, found {sorted(actual_names)}")

    openings = load_opening_suite()
    matches = [load_match(low, high, openings) for low, high in MATCHUPS]
    games = [game for match in matches for game in match["games"]]
    if len(games) != 400:
        raise ValueError(f"Expected 400 games, found {len(games)}")

    rng = np.random.default_rng(SEED)
    matchup_rows = []
    bootstrap_by_match: dict[str, np.ndarray] = {}
    raw_p_values = []
    for match in matches:
        game_scores = np.array([game["low_score"] for game in match["games"]])
        score = float(game_scores.mean())
        boot = bootstrap_scores(match["clusters"], rng)
        bootstrap_by_match[match["stem"]] = boot
        boot_gap = np.array([-logistic_elo(value) for value in boot])
        nominal_gap = match["high"] - match["low"]
        wins = int(np.count_nonzero(game_scores == 1.0))
        draws = int(np.count_nonzero(game_scores == 0.5))
        losses = int(np.count_nonzero(game_scores == 0.0))
        white_scores = [game["low_score"] for game in match["games"] if game["low_color"] == "White"]
        black_scores = [game["low_score"] for game in match["games"] if game["low_color"] == "Black"]
        terminations = Counter(game["termination"] for game in match["games"])
        realized_gap = -logistic_elo(score)
        matchup_rows.append(
            {
                "matchup": match["stem"],
                "low_player": f"MAIA3 {match['low']}",
                "high_player": f"MAIA3 {match['high']}",
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "low_score": score,
                "low_score_ci95_low": percentile(boot, 2.5),
                "low_score_ci95_high": percentile(boot, 97.5),
                "low_white_score": float(np.mean(white_scores)),
                "low_black_score": float(np.mean(black_scores)),
                "nominal_gap": nominal_gap,
                "higher_realized_elo_gap": realized_gap,
                "higher_realized_elo_gap_ci95_low": percentile(boot_gap, 2.5),
                "higher_realized_elo_gap_ci95_high": percentile(boot_gap, 97.5),
                "compression_ratio": realized_gap / nominal_gap,
                "compression_ratio_ci95_low": percentile(boot_gap, 2.5) / nominal_gap,
                "compression_ratio_ci95_high": percentile(boot_gap, 97.5) / nominal_gap,
                "mean_plies": float(np.mean([game["plies"] for game in match["games"]])),
                "median_plies": float(np.median([game["plies"] for game in match["games"]])),
                "min_plies": min(game["plies"] for game in match["games"]),
                "max_plies": max(game["plies"] for game in match["games"]),
                "termination_distribution": json.dumps(dict(sorted(terminations.items())), sort_keys=True),
                "config_hash": match["config_hash"],
                "pgn_sha256": sha256(match["path"]),
            }
        )
        raw_p_values.append(sign_flip_p(match["clusters"], rng))

    adjusted_p_values = holm(raw_p_values)
    pvalue_rows = []
    for match, raw_p, adjusted_p in zip(matches, raw_p_values, adjusted_p_values):
        pvalue_rows.append(
            {
                "matchup": match["stem"],
                "alternative": "two-sided around 50%",
                "raw_p": raw_p,
                "holm_p": adjusted_p,
                "permutations": PERMUTATIONS,
            }
        )

    bt = bt_strengths(matches)
    bt_slopes = np.empty(BOOTSTRAPS)
    for index in range(BOOTSTRAPS):
        sampled_scores = []
        for match in matches:
            clusters = match["clusters"]
            sampled = rng.integers(0, 100, size=100)
            sampled_scores.append(float(clusters[sampled].mean()))
        bt_slopes[index] = slope(bt_strengths(matches, sampled_scores))
    bt_summary = {
        "relative_elo": {"1600": float(bt[0]), "2100": float(bt[1]), "2300": float(bt[2])},
        "strength_on_label_slope": slope(bt),
        "slope_ci95_low": percentile(bt_slopes, 2.5),
        "slope_ci95_high": percentile(bt_slopes, 97.5),
        "fit_note": "Saturated two-edge fit; the 2100-vs-2300 difference is indirect through 1600.",
    }
    davidson = fit_davidson(matches)
    bayesianelo_path = shutil.which("bayeselo") or shutil.which("BayesianElo")

    game_rows = []
    for game in games:
        row = dict(game)
        row["low_score"] = f"{game['low_score']:.1f}"
        game_rows.append(row)
    write_csv("games.csv", game_rows)
    write_csv("matchups.csv", matchup_rows)
    write_csv("pvalues.csv", pvalue_rows)

    all_terminations = Counter(game["termination"] for game in games)
    integrity = {
        "valid": True,
        "expected_pgns_only": True,
        "pgns": len(matches),
        "games": len(games),
        "games_per_pgn": 200,
        "rounds_per_pgn": "1..200 exactly in order",
        "opening_indices_per_pgn": "1..100 exactly twice",
        "opening_pairs_color_reversed": True,
        "one_nonempty_config_hash_per_matchup": True,
        "all_results_resolved": True,
        "expected_player_labels_and_ratings": True,
        "opening_suite_name": EXPECTED_SUITE_NAME,
        "opening_suite_sha256": sha256(SUITE),
        "all_games_match_frozen_opening_prefix": True,
        "game_or_tool_failures": 0,
        "ply_300_cutoffs": 0,
        "max_observed_plies": max(game["plies"] for game in games),
        "config_hashes": {match["stem"]: match["config_hash"] for match in matches},
        "pgn_sha256": {match["path"].name: sha256(match["path"]) for match in matches},
    }
    summary = {
        "analysis_seed": SEED,
        "bootstrap_replicates": BOOTSTRAPS,
        "sign_flip_permutations": PERMUTATIONS,
        "integrity": integrity,
        "matchups": matchup_rows,
        "pvalues": pvalue_rows,
        "bradley_terry": bt_summary,
        "davidson": davidson,
        "bayesianelo": {
            "available": bayesianelo_path is not None,
            "path": bayesianelo_path,
            "status": "not available; sensitivity omitted" if bayesianelo_path is None else "available but not invoked",
        },
        "all_termination_distribution": dict(sorted(all_terminations.items())),
        "all_games_mean_plies": float(np.mean([game["plies"] for game in games])),
        "all_games_median_plies": float(np.median([game["plies"] for game in games])),
    }
    (OUTPUT / "integrity.json").write_text(json.dumps(integrity, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    checksum_files = sorted(path for path in OUTPUT.iterdir() if path.name != "SHA256SUMS")
    with (OUTPUT / "SHA256SUMS").open("w", encoding="utf-8") as handle:
        for path in checksum_files:
            handle.write(f"{sha256(path)}  {path.name}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
