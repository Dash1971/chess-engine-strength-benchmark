from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def wilson(successes: float, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return (math.nan, math.nan)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - spread, center + spread


def build_report(results_dir: Path, output_dir: Path) -> Path:
    pair_stats = defaultdict(
        lambda: {"records": 0, "games": 0, "unresolved": 0,
                 "a_wins": 0, "draws": 0, "b_wins": 0,
                 "opening_scores": defaultdict(list), "termination_counts": Counter(),
                 "cutoffs": 0, "non_cutoff_games": 0, "non_cutoff_score": 0.0}
    )
    for path in sorted(results_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                a, b = sorted((row["white"], row["black"]))
                stats = pair_stats[(a, b)]
                stats["records"] += 1
                stats["termination_counts"][row.get("termination", "unknown")] += 1
                if row["result"] == "1/2-1/2":
                    stats["draws"] += 1
                    a_score = 0.5
                elif (row["result"] == "1-0" and row["white"] == a) or (
                    row["result"] == "0-1" and row["black"] == a
                ):
                    stats["a_wins"] += 1
                    a_score = 1.0
                elif row["result"] in {"1-0", "0-1"}:
                    stats["b_wins"] += 1
                    a_score = 0.0
                else:
                    stats["unresolved"] += 1
                    continue
                stats["games"] += 1
                stats["opening_scores"][row["opening_id"]].append(a_score)
                if row.get("termination") == "max_plies":
                    stats["cutoffs"] += 1
                else:
                    stats["non_cutoff_games"] += 1
                    stats["non_cutoff_score"] += a_score
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "matchups.csv"
    rows = []
    for (a, b), stats in sorted(pair_stats.items()):
        opening_scores = stats.pop("opening_scores")
        termination_counts = stats.pop("termination_counts")
        games = stats["games"]
        score = stats["a_wins"] + stats["draws"] / 2
        low, high = wilson(score, games)
        cluster_means = [sum(values) / len(values) for values in opening_scores.values()]
        paired_low, paired_high = paired_interval(cluster_means)
        dropped_score = (
            stats["non_cutoff_score"] / stats["non_cutoff_games"]
            if stats["non_cutoff_games"] else math.nan
        )
        rows.append({"profile_a": a, "profile_b": b, **stats,
                     "a_score_pct": 100 * score / games if games else math.nan,
                     "dropped_cutoff_a_score_pct": 100 * dropped_score,
                     "termination_histogram": json.dumps(termination_counts, sort_keys=True),
                     "approx_wilson_ci95_low_pct": 100 * low,
                     "approx_wilson_ci95_high_pct": 100 * high,
                     "paired_ci95_low_pct": 100 * paired_low,
                     "paired_ci95_high_pct": 100 * paired_high})
    fields = list(rows[0]) if rows else ["profile_a", "profile_b"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    markdown = output_dir / "REPORT.md"
    markdown.write_text(
        "# Maia engine strength benchmark\n\n"
        f"Completed matchup rows: {len(rows)}. See `matchups.csv` for W/D/L, score, "
        "approximate Wilson intervals, termination histograms, cutoff sensitivity, and "
        "primary opening-pair clustered 95% intervals. Maximum-ply games are scored as draws.\n",
        encoding="utf-8",
    )
    return markdown


def paired_interval(values: list[float], z: float = 1.959963984540054) -> tuple[float, float]:
    """Normal interval over independent opening-pair means (the clustering unit)."""
    if not values:
        return (math.nan, math.nan)
    mean = sum(values) / len(values)
    if len(values) == 1:
        return (math.nan, math.nan)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    spread = z * math.sqrt(variance / len(values))
    return max(0.0, mean - spread), min(1.0, mean + spread)
