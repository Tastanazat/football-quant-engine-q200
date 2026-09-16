"""
Q200 Engine - Odds Reader Tests

Q200 V3.1
"""

from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.odds_reader import (
    read_odds_csv,
    read_odds_dict,
    read_odds_file,
)


def create_csv(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_read_odds_csv(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "DRAW,3.40\n"
            "AWAY,3.80\n"
        ),
    )

    rows = read_odds_csv(
        file_path
    )

    assert len(rows) == 3
    assert rows[0]["outcome"] == "HOME"
    assert rows[0]["odds"] == 2.10
    assert rows[1]["outcome"] == "DRAW"
    assert rows[1]["odds"] == 3.40
    assert rows[2]["outcome"] == "AWAY"
    assert rows[2]["odds"] == 3.80


def test_odds_headers_are_normalized(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            " OUTCOME , ODDS \n"
            "home,2.10\n"
        ),
    )

    rows = read_odds_csv(
        file_path
    )

    assert rows[0]["outcome"] == "HOME"
    assert rows[0]["odds"] == 2.10


def test_read_odds_dict(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "DRAW,3.40\n"
            "AWAY,3.80\n"
        ),
    )

    odds = read_odds_dict(
        file_path
    )

    assert odds == {
        "HOME": 2.10,
        "DRAW": 3.40,
        "AWAY": 3.80,
    }


def test_duplicate_outcome_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "HOME,2.20\n"
        ),
    )

    with pytest.raises(ValueError):
        read_odds_dict(
            file_path
        )


def test_missing_required_header_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,price\n"
            "HOME,2.10\n"
        ),
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_unknown_header_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds,team\n"
            "HOME,2.10,A\n"
        ),
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_invalid_odds_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "HOME,1.00\n"
        ),
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_non_numeric_odds_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "HOME,abc\n"
        ),
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_empty_odds_file_is_rejected(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        "",
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_missing_odds_file_is_rejected(tmp_path):
    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        read_odds_file(
            file_path
        )


def test_unsupported_odds_extension_is_rejected(tmp_path):
    file_path = tmp_path / "odds.txt"

    file_path.write_text(
        "outcome,odds\nHOME,2.10\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        read_odds_file(
            file_path
        )


def test_xlsx_odds_reader(tmp_path):
    openpyxl = pytest.importorskip(
        "openpyxl"
    )

    file_path = tmp_path / "odds.xlsx"

    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    worksheet.append(
        [
            "outcome",
            "odds",
        ]
    )

    worksheet.append(
        [
            "HOME",
            2.10,
        ]
    )

    worksheet.append(
        [
            "DRAW",
            3.40,
        ]
    )

    worksheet.append(
        [
            "AWAY",
            3.80,
        ]
    )

    workbook.save(
        file_path
    )

    rows = read_odds_file(
        file_path
    )

    assert len(rows) == 3
    assert rows[0]["outcome"] == "HOME"
    assert rows[0]["odds"] == 2.10


def test_mixed_case_outcome_is_normalized(tmp_path):
    file_path = tmp_path / "odds.csv"

    create_csv(
        file_path,
        (
            "outcome,odds\n"
            "home,2.10\n"
            "Draw,3.40\n"
            "away,3.80\n"
        ),
    )

    odds = read_odds_dict(
        file_path
    )

    assert "HOME" in odds
    assert "DRAW" in odds
    assert "AWAY" in odds
