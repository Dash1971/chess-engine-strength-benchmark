#!/usr/bin/env python3
"""Generate the supplemental appendix's SVG figures from published data."""

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
NOMINAL = "#64748b"
REALIZED = "#2563eb"
SUCCESS = "#0f766e"
WARNING = "#b45309"


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


def circle(cx: float, cy: float, radius: float, fill: str, stroke: str, width: float) -> str:
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{width:.1f}"/>'
    )


def document(title: str, description: str, height: int, body: list[str]) -> str:
    styles = f"""
      .title {{ font: 700 30px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .subtitle {{ font: 400 19px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
      .label {{ font: 600 20px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .value {{ font: 700 21px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {TEXT}; }}
      .small {{ font: 400 17px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
      .tiny {{ font: 500 15px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {MUTED}; }}
      .inverse {{ font: 700 23px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #ffffff; }}
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


def compression_chart(matchups: list[dict[str, str]]) -> str:
    x0, bar_width, maximum = 260.0, 600.0, 700.0
    body = [
        text(40, 48, "Nominal high-rating gaps versus realized gaps", "title"),
        text(40, 82, "The score-to-Elo separation was much smaller than the conditioning-label gap.", "subtitle"),
    ]
    for tick in (0, 200, 400, 600, 700):
        x = x0 + bar_width * tick / maximum
        body.append(line(x, 105, x, 410, GRID, 1, "5 6" if tick not in {0, 700} else None))
        body.append(text(x, 438, tick, "small", "middle"))
    body.append(text(860, 468, "Elo points", "small", "end"))

    for index, row in enumerate(matchups):
        y = 130 + index * 145
        low = row["low_player"].split()[-1]
        high = row["high_player"].split()[-1]
        nominal = float(row["nominal_gap"])
        realized = float(row["higher_realized_elo_gap"])
        compression = 100.0 * float(row["compression_ratio"])
        body.extend([
            text(40, y + 18, f"{low}–{high}", "label"),
            text(x0 - 16, y + 19, "Nominal", "small", "end"),
            rect(x0, y, bar_width * nominal / maximum, 28, NOMINAL, 5),
            text(x0 + bar_width * nominal / maximum + 12, y + 21, f"{nominal:.0f}", "value"),
            text(x0 - 16, y + 65, "Realized", "small", "end"),
            rect(x0, y + 46, bar_width * realized / maximum, 28, REALIZED, 5),
            text(x0 + bar_width * realized / maximum + 12, y + 67, f"{realized:.1f}", "value"),
            text(x0, y + 105, f"{compression:.1f}% of nominal gap preserved", "small"),
        ])
    return document(
        "High-rating nominal and realized gaps",
        "The nominal 500-point gap from 1600 to 2100 produced a realized 260.5 Elo gap, while the nominal 700-point gap from 1600 to 2300 produced a realized 246.3 Elo gap.",
        490,
        body,
    )


def score_interval_chart(matchups: list[dict[str, str]]) -> str:
    left, right, top, bottom = 220.0, 875.0, 120.0, 365.0
    maximum = 0.5

    def x_pos(score: float) -> float:
        return left + (right - left) * score / maximum

    body = [
        text(40, 48, "The 1600 profile scored far below 50%", "title"),
        text(40, 82, "Points show observed score; whiskers show paired-opening bootstrap 95% intervals.", "subtitle"),
    ]
    for tick in (0, 10, 20, 30, 40, 50):
        x = x_pos(tick / 100.0)
        body.append(line(x, top, x, bottom, SUCCESS if tick == 50 else GRID, 2 if tick == 50 else 1, "7 6" if tick == 50 else None))
        body.append(text(x, 398, f"{tick}%", "small", "middle"))
    body.append(text(right, 108, "50% = even", "small", "end"))

    for index, row in enumerate(matchups):
        y = 185 + index * 115
        high = row["high_player"].split()[-1]
        score = float(row["low_score"])
        low_ci = float(row["low_score_ci95_low"])
        high_ci = float(row["low_score_ci95_high"])
        x_low, x_mid, x_high = x_pos(low_ci), x_pos(score), x_pos(high_ci)
        body.extend([
            text(40, y + 7, f"1600 vs {high}", "label"),
            line(x_low, y, x_high, y, REALIZED, 6),
            line(x_low, y - 13, x_low, y + 13, REALIZED, 4),
            line(x_high, y - 13, x_high, y + 13, REALIZED, 4),
            circle(x_mid, y, 12, BG, REALIZED, 6),
            text(x_mid, y - 25, f"{score * 100:.2f}%", "value", "middle"),
            text(x_mid, y + 37, f"{low_ci * 100:.2f}–{high_ci * 100:.2f}%", "tiny", "middle"),
        ])
    body.append(text(40, 455, "Both intervals are far from 50% and overlap substantially with each other.", "label"))
    return document(
        "Maia 3 1600 score against higher labels",
        "The 1600 profile scored 18.25 percent against 2100 with a 13.75 to 23.00 percent interval, and 19.50 percent against 2300 with a 15.00 to 24.00 percent interval. Both are far below 50 percent and the intervals overlap.",
        485,
        body,
    )


def design_chart(matchups: list[dict[str, str]]) -> str:
    by_high = {int(row["high_player"].split()[-1]): row for row in matchups}
    x_anchor, x_high = 190.0, 740.0
    y_anchor, y_2100, y_2300 = 265.0, 155.0, 375.0
    body = [
        text(40, 48, "What the follow-up directly tested", "title"),
        text(40, 82, "Two 200-game edges share the 1600 anchor; the higher labels never played each other.", "subtitle"),
        line(x_anchor + 72, y_anchor - 15, x_high - 72, y_2100 + 15, REALIZED, 6),
        line(x_anchor + 72, y_anchor + 15, x_high - 72, y_2300 - 15, REALIZED, 6),
    ]
    for high, y, edge_y in ((2100, y_2100, 174), (2300, y_2300, 348)):
        row = by_high[high]
        gap = float(row["higher_realized_elo_gap"])
        body.extend([
            rect(365, edge_y - 28, 240, 58, BG, 10),
            text(485, edge_y - 2, "200 games", "small", "middle"),
            text(485, edge_y + 21, f"+{gap:.1f} realized Elo", "tiny", "middle"),
            circle(x_high, y, 72, TRACK, REALIZED, 5),
            text(x_high, y - 7, f"Label {high}", "label", "middle"),
            text(x_high, y + 24, "higher profile", "small", "middle"),
        ])
    body.extend([
        circle(x_anchor, y_anchor, 78, REALIZED, REALIZED, 5),
        text(x_anchor, y_anchor - 5, "Label 1600", "inverse", "middle"),
        text(x_anchor, y_anchor + 28, "shared anchor", "inverse", "middle"),
        line(x_high, y_2100 + 74, x_high, y_2300 - 74, WARNING, 4, "8 7"),
        circle(x_high, y_anchor, 21, BG, WARNING, 4),
        text(x_high, y_anchor + 8, "×", "value", "middle"),
        text(925, y_anchor - 5, "No direct", "label", "end"),
        text(925, y_anchor + 24, "2100–2300 match", "small", "end"),
        text(40, 485, "Therefore the appendix cannot establish whether 2300 is stronger than 2100.", "label"),
    ])
    return document(
        "Sparse shared-anchor study design",
        "The study directly compared 1600 with 2100 and 1600 with 2300 in 200 games each. It did not directly compare 2100 with 2300, so it cannot order those two higher profiles.",
        515,
        body,
    )


def main() -> None:
    matchups = rows("matchups.csv")
    if len(matchups) != 2:
        raise ValueError(f"Expected exactly two matchups, found {len(matchups)}")
    matchups.sort(key=lambda row: int(row["high_player"].split()[-1]))
    FIGURES.mkdir(exist_ok=True)
    outputs = {
        "high-rating-compression.svg": compression_chart(matchups),
        "score-intervals.svg": score_interval_chart(matchups),
        "study-design.svg": design_chart(matchups),
    }
    for name, content in outputs.items():
        (FIGURES / name).write_text(content, encoding="utf-8")
        print(f"Wrote figures/{name}")


if __name__ == "__main__":
    main()
