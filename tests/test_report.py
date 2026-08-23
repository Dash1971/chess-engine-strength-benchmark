import csv
import json
from pathlib import Path

from maia_benchmark.report import build_report


def test_unresolved_records_do_not_enter_wdl_denominator(tmp_path: Path):
    raw = tmp_path / "raw"
    output = tmp_path / "report"
    raw.mkdir()
    rows = [
        {"white": "a", "black": "b", "opening_id": 1, "result": "1-0"},
        {"white": "b", "black": "a", "opening_id": 1, "result": "*"},
    ]
    (raw / "a__vs__b.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )

    build_report(raw, output)
    with (output / "matchups.csv").open(newline="", encoding="utf-8") as handle:
        result = next(csv.DictReader(handle))

    assert result["records"] == "2"
    assert result["games"] == "1"
    assert result["unresolved"] == "1"
    assert result["a_wins"] == "1"
    assert result["a_score_pct"] == "100.0"
