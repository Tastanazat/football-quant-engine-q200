"""
Q200 Engine - File Pipeline Tests

Q200 V3.1
"""

from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.file_pipeline import run_pipeline_from_files


def create_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_run_pipeline_from_two_csv_files(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.80,1.10,1.40\n",
    )

    create_csv(
        file_2,
        "away_ga,home_xg,home_xga,away_xga\n"
        "1.30,1.75,1.05,1.25\n",
    )

    result = run_pipeline_from_files(
        file_1,
        file_2,
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True
    assert result.snapshot.model_version == "Q200-V3.1"
    assert result.snapshot.lambda_home > 0
    assert result.snapshot.lambda_away > 0
    assert isinstance(result.selections, list)


def test_file_1_values_reach_model(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "2.00,1.00,1.50\n",
    )

    create_csv(
        file_2,
        "home_gf,home_ga,away_gf,away_ga\n"
        "1.00,2.00,0.50,1.40\n",
    )

    result = run_pipeline_from_files(
        file_1,
        file_2,
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True
    assert result.snapshot.lambda_home > 0
    assert result.snapshot.lambda_away > 0


def test_mixed_csv_xlsx_files(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")

    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.xlsx"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.80,1.10,1.40\n",
    )

    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    worksheet.append(
        [
            "away_ga",
            "home_xg",
            "home_xga",
            "away_xga",
        ]
    )

    worksheet.append(
        [
            1.30,
            1.75,
            1.05,
            1.25,
        ]
    )

    workbook.save(file_2)

    result = run_pipeline_from_files(
        file_1,
        file_2,
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True


def test_row_indexes_are_forwarded(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.00,2.00,3.00\n"
        "2.00,3.00,4.00\n",
    )

    create_csv(
        file_2,
        "away_ga\n"
        "1.10\n"
        "1.30\n",
    )

    result = run_pipeline_from_files(
        file_1,
        file_2,
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
        row_index_1=1,
        row_index_2=1,
    )

    assert result.snapshot.locked is True


def test_file_pipeline_rejects_invalid_odds(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.80,1.10,1.40\n",
    )

    create_csv(
        file_2,
        "away_ga\n"
        "1.30\n",
    )

    with pytest.raises(ValueError):
        run_pipeline_from_files(
            file_1,
            file_2,
            {
                "HOME": 1.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            bankroll=50_000,
        )


def test_file_pipeline_rejects_invalid_bankroll(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.80,1.10,1.40\n",
    )

    create_csv(
        file_2,
        "away_ga\n"
        "1.30\n",
    )

    with pytest.raises(ValueError):
        run_pipeline_from_files(
            file_1,
            file_2,
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            bankroll=0,
        )
