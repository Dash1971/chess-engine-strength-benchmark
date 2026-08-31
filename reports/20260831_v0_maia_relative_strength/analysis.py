#!/usr/bin/env python3
"""Reproduce the Maia relative-strength report tables from the published PGNs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import chess.pgn
import numpy as np
from scipy.optimize import minimize


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RATINGS = np.array([1100, 1300, 1500, 1700, 1900], dtype=float)
BOOTSTRAPS = 20_000
PERMUTATIONS = 100_000
SEED = 20260831
ELO_SCALE = 400.0 / math.log(10.0)
SLUG_RE = re.compile(r"(maia[23])-(\d+)__vs__(maia[23])-(\d+)\.pgn$")


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q, method="linear"))


def logistic_elo(score: float) -> float:
    if score <= 0:
        return -math.inf
    if score >= 1:
        return math.inf
    return 400.0 * math.log10(score / (1.0 - score))


def score_for(result: str, is_white: bool) -> float:
    if result == "1/2-1/2":
        return 0.5
    return 1.0 if (result == "1-0") == is_white else 0.0


def read_match(path: Path) -> dict:
    match = SLUG_RE.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unexpected PGN name: {path.name}")
    family_a, rating_a, family_b, rating_b = match.groups()
    rating_a, rating_b = int(rating_a), int(rating_b)
    expected_a = f"{family_a.upper()} {rating_a}"
    expected_b = f"{family_b.upper()} {rating_b}"
    games = []
    with path.open(encoding="utf-8") as handle:
        while game := chess.pgn.read_game(handle):
            h = game.headers
            result = h.get("Result")
            if result not in {"1-0", "0-1", "1/2-1/2"}:
                raise ValueError(f"Unresolved result in {path.name}: {result}")
            white, black = h.get("White"), h.get("Black")
            if {white, black} != {expected_a, expected_b}:
                raise ValueError(f"Unexpected players in {path.name}: {white}, {black}")
            opening = int(h["OpeningIndex"])
            a_white = white == expected_a
            board = game.board()
            plies = 0
            for move in game.mainline_moves():
                board.push(move)
                plies += 1
            games.append({
                "matchup": path.stem,
                "round": int(h["Round"]),
                "opening_index": opening,
                "engine_a": expected_a,
                "engine_b": expected_b,
                "engine_a_family": family_a,
                "engine_b_family": family_b,
                "engine_a_rating": rating_a,
                "engine_b_rating": rating_b,
                "engine_a_color": "White" if a_white else "Black",
                "white": white,
                "black": black,
                "result": result,
                "engine_a_score": score_for(result, a_white),
                "termination": h.get("Termination", "unknown"),
                "plies": plies,
                "config_hash": h.get("ConfigHash", ""),
                "opening_suite": h.get("OpeningSuite", ""),
                "source_pgn": path.name,
            })
    if len(games) != 200:
        raise ValueError(f"{path.name}: expected 200 games, found {len(games)}")
    rounds = [g["round"] for g in games]
    if rounds != list(range(1, 201)):
        raise ValueError(f"{path.name}: rounds are not exactly 1..200")
    by_opening = defaultdict(list)
    for game in games:
        by_opening[game["opening_index"]].append(game)
    if set(by_opening) != set(range(1, 101)):
        raise ValueError(f"{path.name}: opening indices are not exactly 1..100")
    for opening, pair in by_opening.items():
        if len(pair) != 2 or {g["engine_a_color"] for g in pair} != {"White", "Black"}:
            raise ValueError(f"{path.name}: opening {opening} is not color reversed")
    if len({g["config_hash"] for g in games}) != 1:
        raise ValueError(f"{path.name}: multiple configuration hashes")
    return {
        "path": path,
        "family_a": family_a,
        "family_b": family_b,
        "rating_a": rating_a,
        "rating_b": rating_b,
        "engine_a": expected_a,
        "engine_b": expected_b,
        "games": games,
        "clusters": np.array([
            [g["engine_a_score"] for g in sorted(by_opening[i], key=lambda x: x["round"])]
            for i in range(1, 101)
        ], dtype=float),
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
    m = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def fit_bt(edge_points: list[tuple[int, int, float, float]]) -> np.ndarray:
    """Bradley-Terry MLE; draws enter as half a point."""
    x = np.zeros(5)
    for _ in range(80):
        gradient = np.zeros(4)
        information = np.zeros((4, 4))
        for i, j, points_i, games in edge_points:
            p = 1.0 / (1.0 + math.exp(-(x[i] - x[j])))
            g = points_i - games * p
            w = games * p * (1.0 - p)
            vector = np.zeros(4)
            if i:
                vector[i - 1] += 1.0
            if j:
                vector[j - 1] -= 1.0
            gradient += g * vector
            information += w * np.outer(vector, vector)
        step = np.linalg.solve(information, gradient)
        x[1:] += step
        if float(np.max(np.abs(step))) < 1e-11:
            break
    return x * ELO_SCALE


def slope(ratings: np.ndarray, strengths: np.ndarray) -> float:
    return float(np.polyfit(ratings, strengths, 1)[0])


def fit_davidson(edges: list[dict]) -> tuple[np.ndarray, float, float]:
    """Davidson draw-aware MLE with rating 1100 fixed to zero."""
    def objective(params: np.ndarray) -> float:
        x = np.r_[0.0, params[:4]]
        nu = math.exp(float(params[4]))
        ll = 0.0
        for edge in edges:
            i, j = edge["i"], edge["j"]
            ai, aj = math.exp(x[i]), math.exp(x[j])
            draw_weight = nu * math.sqrt(ai * aj)
            total = ai + aj + draw_weight
            ll += edge["wins"] * math.log(ai / total)
            ll += edge["losses"] * math.log(aj / total)
            ll += edge["draws"] * math.log(draw_weight / total)
        return -ll

    result = minimize(objective, np.zeros(5), method="BFGS", options={"gtol": 1e-10, "maxiter": 2000})
    # BFGS can report finite-difference precision loss at an already stationary
    # solution; reject only a materially non-zero terminal gradient.
    if not result.success and float(np.linalg.norm(result.jac)) > 5e-5:
        raise RuntimeError(f"Davidson fit failed: {result.message}; gradient={result.jac}")
    strengths = np.r_[0.0, result.x[:4]] * ELO_SCALE
    return strengths, math.exp(float(result.x[4])), float(result.fun)


def write_csv(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    with (DATA / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pgns = sorted(DATA.glob("*.pgn"))
    if len(pgns) != 15:
        raise SystemExit(f"Expected 15 PGNs, found {len(pgns)}")
    matches = [read_match(path) for path in pgns]
    all_games = [game for match in matches for game in match["games"]]
    if len(all_games) != 3000:
        raise AssertionError("Expected 3,000 games")

    game_rows = []
    for game in all_games:
        row = dict(game)
        row["engine_a_score"] = f'{game["engine_a_score"]:.1f}'
        game_rows.append(row)
    write_csv("games.csv", game_rows)

    rng = np.random.default_rng(SEED)
    matchup_rows = []
    p_records = []
    for match in matches:
        games = match["games"]
        scores = np.array([g["engine_a_score"] for g in games])
        boot = bootstrap_scores(match["clusters"], rng)
        low, high = percentile(boot, 2.5), percentile(boot, 97.5)
        wins = int(np.count_nonzero(scores == 1))
        draws = int(np.count_nonzero(scores == 0.5))
        losses = int(np.count_nonzero(scores == 0))
        score = float(scores.mean())
        white_scores = [g["engine_a_score"] for g in games if g["engine_a_color"] == "White"]
        black_scores = [g["engine_a_score"] for g in games if g["engine_a_color"] == "Black"]
        nominal_gap = match["rating_b"] - match["rating_a"] if match["family_a"] == match["family_b"] else ""
        realized_gap = -logistic_elo(score) if nominal_gap != "" else ""
        row = {
            "matchup": match["path"].stem,
            "engine_a": match["engine_a"],
            "engine_b": match["engine_b"],
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "engine_a_score": f"{score:.6f}",
            "ci95_low": f"{low:.6f}",
            "ci95_high": f"{high:.6f}",
            "engine_a_realized_elo": f"{logistic_elo(score):.3f}",
            "engine_a_white_score": f"{np.mean(white_scores):.6f}",
            "engine_a_black_score": f"{np.mean(black_scores):.6f}",
            "nominal_gap": nominal_gap,
            "higher_rated_realized_gap": f"{realized_gap:.3f}" if realized_gap != "" else "",
            "compression_ratio": f"{realized_gap / nominal_gap:.6f}" if nominal_gap != "" else "",
            "mean_plies": f"{np.mean([g['plies'] for g in games]):.3f}",
            "median_plies": f"{np.median([g['plies'] for g in games]):.1f}",
            "config_hash": games[0]["config_hash"],
            "pgn": match["path"].name,
        }
        matchup_rows.append(row)
        if match["family_a"] == match["family_b"] and abs(match["rating_b"] - match["rating_a"]) == 200:
            family = f"{match['family_a']}_adjacent"
        elif match["family_a"] != match["family_b"]:
            family = "cross_generation"
        else:
            family = "endpoint_unadjusted"
        p_records.append({
            "matchup": match["path"].stem,
            "family": family,
            "raw_p": sign_flip_p(match["clusters"], rng),
        })
    for family in ("maia2_adjacent", "maia3_adjacent", "cross_generation"):
        group = [record for record in p_records if record["family"] == family]
        adjusted = holm([record["raw_p"] for record in group])
        for record, value in zip(group, adjusted):
            record["holm_p"] = value
    for record in p_records:
        record.setdefault("holm_p", record["raw_p"])
    write_csv("matchups.csv", matchup_rows)
    write_csv("pvalues.csv", [{
        **record,
        "raw_p": f'{record["raw_p"]:.8f}',
        "holm_p": f'{record["holm_p"]:.8f}',
    } for record in p_records])

    family_edges = {}
    bt_rows, bt_fit_rows, family_rows = [], [], []
    family_boot = {}
    for family in ("maia2", "maia3"):
        internal = [m for m in matches if m["family_a"] == family and m["family_b"] == family]
        edges = []
        for match in internal:
            scores = np.array([g["engine_a_score"] for g in match["games"]])
            edges.append({
                "match": match,
                "i": int(np.where(RATINGS == match["rating_a"])[0][0]),
                "j": int(np.where(RATINGS == match["rating_b"])[0][0]),
                "wins": int(np.count_nonzero(scores == 1)),
                "draws": int(np.count_nonzero(scores == 0.5)),
                "losses": int(np.count_nonzero(scores == 0)),
                "points": float(scores.sum()),
            })
        family_edges[family] = edges
        bt_input = [(e["i"], e["j"], e["points"], 200.0) for e in edges]
        strengths = fit_bt(bt_input)
        bt_slope = slope(RATINGS, strengths)
        davidson_strengths, draw_nu, davidson_nll = fit_davidson(edges)
        davidson_slope = slope(RATINGS, davidson_strengths)
        for rating, strength, d_strength in zip(RATINGS.astype(int), strengths, davidson_strengths):
            bt_rows.append({
                "family": family,
                "nominal_rating": rating,
                "bt_relative_elo": f"{strength:.3f}",
                "davidson_relative_elo": f"{d_strength:.3f}",
            })
        residuals = []
        for edge in edges:
            fitted = 1.0 / (1.0 + 10.0 ** ((strengths[edge["j"]] - strengths[edge["i"]]) / 400.0))
            observed = edge["points"] / 200.0
            residuals.append(observed - fitted)
            bt_fit_rows.append({
                "family": family,
                "matchup": edge["match"]["path"].stem,
                "observed_engine_a_score": f"{observed:.6f}",
                "fitted_engine_a_score": f"{fitted:.6f}",
                "residual_percentage_points": f"{100 * (observed - fitted):.3f}",
            })
        boot_slopes = np.empty(BOOTSTRAPS)
        for b in range(BOOTSTRAPS):
            sampled_edges = []
            for edge in edges:
                clusters = edge["match"]["clusters"]
                idx = rng.integers(0, 100, size=100)
                points = float(clusters[idx].sum())
                sampled_edges.append((edge["i"], edge["j"], points, 200.0))
            boot_slopes[b] = slope(RATINGS, fit_bt(sampled_edges))
        family_boot[family] = boot_slopes
        family_rows.append({
            "family": family,
            "bt_slope": f"{bt_slope:.6f}",
            "bt_slope_ci95_low": f"{percentile(boot_slopes, 2.5):.6f}",
            "bt_slope_ci95_high": f"{percentile(boot_slopes, 97.5):.6f}",
            "davidson_slope": f"{davidson_slope:.6f}",
            "davidson_draw_nu": f"{draw_nu:.6f}",
            "davidson_nll": f"{davidson_nll:.3f}",
            "bt_fit_rmse_percentage_points": f"{100 * math.sqrt(np.mean(np.square(residuals))):.3f}",
        })
    difference = family_boot["maia3"] - family_boot["maia2"]
    observed_difference = float(family_rows[1]["bt_slope"]) - float(family_rows[0]["bt_slope"])
    slope_p = 2.0 * min((np.count_nonzero(difference <= 0) + 1) / (BOOTSTRAPS + 1),
                        (np.count_nonzero(difference >= 0) + 1) / (BOOTSTRAPS + 1))
    family_rows.append({
        "family": "maia3_minus_maia2",
        "bt_slope": f"{observed_difference:.6f}",
        "bt_slope_ci95_low": f"{percentile(difference, 2.5):.6f}",
        "bt_slope_ci95_high": f"{percentile(difference, 97.5):.6f}",
        "davidson_slope": f"{float(family_rows[1]['davidson_slope']) - float(family_rows[0]['davidson_slope']):.6f}",
        "davidson_draw_nu": "",
        "davidson_nll": "",
        "bt_fit_rmse_percentage_points": "",
    })
    write_csv("family_summary.csv", family_rows)
    write_csv("bt_ratings.csv", bt_rows)
    write_csv("bt_fit.csv", bt_fit_rows)

    terminations = Counter(g["termination"] for g in all_games)
    write_csv("terminations.csv", [{
        "termination": key,
        "games": value,
        "percentage": f"{100 * value / len(all_games):.3f}",
    } for key, value in sorted(terminations.items())])

    summary = {
        "games": len(all_games),
        "matchups": len(matches),
        "opening_pairs_per_matchup": 100,
        "bootstrap_replicates": BOOTSTRAPS,
        "sign_flip_permutations": PERMUTATIONS,
        "analysis_seed": SEED,
        "all_results_resolved": True,
        "all_opening_pairs_color_reversed": True,
        "config_hashes": {m["path"].stem: m["games"][0]["config_hash"] for m in matches},
        "terminations": dict(sorted(terminations.items())),
        "mean_plies": float(np.mean([g["plies"] for g in all_games])),
        "median_plies": float(np.median([g["plies"] for g in all_games])),
        "min_plies": min(g["plies"] for g in all_games),
        "max_plies": max(g["plies"] for g in all_games),
        "bt_slope_difference_p": slope_p,
    }
    (DATA / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    checksum_files = sorted(path for path in DATA.iterdir() if path.name != "SHA256SUMS")
    with (DATA / "SHA256SUMS").open("w", encoding="utf-8") as handle:
        for path in checksum_files:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            handle.write(f"{digest}  {path.name}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
