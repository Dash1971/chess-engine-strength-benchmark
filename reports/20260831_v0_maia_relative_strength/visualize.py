#!/usr/bin/env python3
"""Generate the report's SVG figures from its published CSV tables."""

from __future__ import annotations

import csv
import html
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIGURES = HERE / "figures"

WIDTH = 960
BG = "#ffffff"
TEXT = "#172033"
MUTED = "#5b6475"
GRID = "#d8dee9"
TRACK = "#eef2f7"
MAIA2 = "#64748b"
MAIA3 = "#2563eb"
SUCCESS = "#0f766e"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: object, css: str = "label", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="{css}" '
        f'text-anchor="{anchor}">{esc(value)}</text>'
    )


def rect(x: float, y: float, width: float, height: float, fill: str, radius: float = 8) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius:.1f}" fill="{fill}"/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str = GRID,
    width: float = 1,
    dash: str | None = None,
) -> str:
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width:.1f}"{dashed}/>'
    )


def document(title: str, description: str, height: int, body: list[str]) -> str:
    styles = f"""
      .title {{ font: 700 30px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .subtitle {{ font: 400 19px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
      .label {{ font: 600 20px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .value {{ font: 700 21px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .small {{ font: 400 17px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
      .tiny {{ font: 500 15px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
    """
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="chart-title chart-desc">',
        f'  <title id="chart-title">{esc(title)}</title>',
        f'  <desc id="chart-desc">{esc(description)}</desc>',
        f'  <rect width="{WIDTH}" height="{height}" fill="{BG}"/>',
        f'  <style>{styles}</style>',
        *(f"  {item}" for item in body),
        '</svg>',
        '',
    ])


def compression_chart(family_rows: list[dict[str, str]], matchup_rows: list[dict[str, str]]) -> str:
    slopes = {row["family"]: float(row["bt_slope"]) for row in family_rows if row["family"] in {"maia2", "maia3"}}
    endpoints = {}
    for row in matchup_rows:
        if row["nominal_gap"] == "800":
            family = row["engine_a"].split()[0].lower()
            endpoints[family] = {
                "ratio": float(row["compression_ratio"]),
                "gap": round(float(row["higher_rated_realized_gap"])),
            }

    x0, bar_width = 235.0, 640.0
    body = [
        text(40, 48, "How much of the nominal 1100–1900 gap survived?", "title"),
        text(40, 82, "An uncompressed scale would reach 100%.", "subtitle"),
    ]
    for tick in (0, 25, 50, 75, 100):
        x = x0 + bar_width * tick / 100
        body.append(line(x, 108, x, 316, GRID, 1, "5 6" if tick not in {0, 100} else None))
        body.append(text(x, 345, f"{tick}%", "small", "middle"))

    for family, label, color, y in (
        ("maia2", "Maia 2", MAIA2, 140),
        ("maia3", "Maia 3", MAIA3, 240),
    ):
        ratio = endpoints[family]["ratio"]
        gap = endpoints[family]["gap"]
        body.extend([
            text(40, y + 35, label, "label"),
            rect(x0, y, bar_width, 50, TRACK),
            rect(x0, y, bar_width * ratio, 50, color),
            text(x0 + bar_width * ratio + 14, y + 34, f"{ratio * 100:.1f}%", "value"),
            text(x0, y + 77, f"{gap} realized Elo; fitted slope {slopes[family]:.3f}", "small"),
        ])
    body.append(text(40, 388, "Maia 3 preserved about 2.6× as much of the endpoint span.", "label"))
    return document(
        "Endpoint scale preservation",
        "Maia 2 preserved 17.6 percent of the nominal 800-point span while Maia 3 preserved 46.5 percent.",
        420,
        body,
    )


def adjacent_chart(matchup_rows: list[dict[str, str]]) -> str:
    selected: dict[tuple[str, str], float] = {}
    for row in matchup_rows:
        if row["nominal_gap"] != "200":
            continue
        family = row["engine_a"].split()[0].lower()
        low = row["engine_a"].split()[1]
        high = row["engine_b"].split()[1]
        selected[(family, f"{low}–{high}")] = float(row["higher_rated_realized_gap"])

    bands = ["1100–1300", "1300–1500", "1500–1700", "1700–1900"]
    x0, bar_width, maximum = 235.0, 650.0, 140.0
    body = [
        text(40, 48, "Adjacent rating bands: realized separation", "title"),
        text(40, 82, "Each label step is nominally 200 points; longer bars mean clearer separation.", "subtitle"),
    ]
    for tick in (0, 50, 100, 140):
        x = x0 + bar_width * tick / maximum
        body.append(line(x, 112, x, 500, GRID, 1, "5 6" if tick else None))
        body.append(text(x, 530, str(tick), "small", "middle"))
    body.append(text(885, 560, "Realized Elo", "small", "end"))

    for index, band in enumerate(bands):
        y = 130 + index * 94
        body.append(text(40, y + 41, band, "label"))
        for family, label, color, offset in (
            ("maia2", "M2", MAIA2, 0),
            ("maia3", "M3", MAIA3, 36),
        ):
            value = selected[(family, band)]
            length = bar_width * value / maximum
            body.extend([
                text(192, y + offset + 20, label, "tiny", "end"),
                rect(x0, y + offset, bar_width, 25, TRACK, 5),
                rect(x0, y + offset, length, 25, color, 5),
                text(x0 + length + 11, y + offset + 20, f"{value:.0f}", "value"),
            ])
    body.extend([
        rect(40, 558, 22, 22, MAIA2, 4),
        text(74, 576, "Maia 2", "small"),
        rect(180, 558, 22, 22, MAIA3, 4),
        text(214, 576, "Maia 3", "small"),
        text(40, 620, "Maia 2 nearly flattened at 1300–1500 and 1700–1900.", "label"),
    ])
    return document(
        "Adjacent-band realized Elo gaps",
        "Grouped horizontal bars show that all Maia 3 adjacent bands separated more strongly than the corresponding Maia 2 bands.",
        650,
        body,
    )


def same_label_chart(matchup_rows: list[dict[str, str]]) -> str:
    scores: list[tuple[int, float]] = []
    for row in matchup_rows:
        a_family, a_rating = row["engine_a"].split()
        b_family, b_rating = row["engine_b"].split()
        if a_family == "MAIA2" and b_family == "MAIA3" and a_rating == b_rating:
            scores.append((int(a_rating), 100.0 * (1.0 - float(row["engine_a_score"]))))
    scores.sort()

    left, right, top, bottom = 110.0, 895.0, 120.0, 455.0
    y_min, y_max = 45.0, 75.0

    def x_pos(index: int) -> float:
        return left + (right - left) * index / (len(scores) - 1)

    def y_pos(score: float) -> float:
        return bottom - (score - y_min) * (bottom - top) / (y_max - y_min)

    body = [
        text(40, 48, "Maia 3 versus Maia 2 at the same label", "title"),
        text(40, 82, "Maia 3's score rises sharply at the higher rating settings.", "subtitle"),
    ]
    for tick in (50, 55, 60, 65, 70, 75):
        y = y_pos(tick)
        body.append(line(left, y, right, y, SUCCESS if tick == 50 else GRID, 2 if tick == 50 else 1, "7 6" if tick == 50 else None))
        body.append(text(left - 18, y + 7, f"{tick}%", "small", "end"))
    body.append(text(right, y_pos(50) - 12, "50% = even", "small", "end"))

    points = [(x_pos(index), y_pos(score)) for index, (_, score) in enumerate(scores)]
    body.append(
        '<polyline points="{}" fill="none" stroke="{}" stroke-width="5" '
        'stroke-linecap="round" stroke-linejoin="round"/>'.format(
            " ".join(f"{x:.1f},{y:.1f}" for x, y in points), MAIA3
        )
    )
    for index, ((rating, score), (x, y)) in enumerate(zip(scores, points)):
        resolved = rating in {1700, 1900}
        body.extend([
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{MAIA3 if resolved else BG}" '
            f'stroke="{MAIA3}" stroke-width="5"/>',
            text(x, y - 21, f"{score:.2f}%" if score % 1 else f"{score:.1f}%", "value", "middle"),
            text(x, bottom + 40, rating, "label", "middle"),
            text(x, bottom + 69, "clear" if resolved else ("trend" if rating == 1500 else "even"), "tiny", "middle"),
        ])
    body.extend([
        text(40, 566, "Filled points mark statistically resolved Maia 3 advantages.", "small"),
        text(40, 610, "Bottom line: even at 1100–1300, then increasingly Maia 3-favored.", "label"),
    ])
    return document(
        "Maia 3 score against Maia 2 at equal labels",
        "A line rises from roughly 50 percent at 1100 and 1300 to 70.5 percent at 1900, with statistically resolved advantages at 1700 and 1900.",
        640,
        body,
    )


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    family_rows = rows("family_summary.csv")
    matchup_rows = rows("matchups.csv")
    outputs = {
        "compression-overview.svg": compression_chart(family_rows, matchup_rows),
        "adjacent-band-separation.svg": adjacent_chart(matchup_rows),
        "same-label-maia3-score.svg": same_label_chart(matchup_rows),
    }
    for name, content in outputs.items():
        (FIGURES / name).write_text(content, encoding="utf-8")
        print(f"Wrote figures/{name}")


if __name__ == "__main__":
    main()
