"""
Q200 Engine - Statistics Loader Tests

Q200 V3.1
"""

from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.statistics_loader import load_team_stats


def create_csv(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_load_team_stats_from_two_csv_files(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n1.80,1.10,1.40\n",
    )

    create_csv(
        file_2,
        "away_ga,home_xg,home_xga,away_xga\n"
        "1.30,1.75,1.05,1.25\n",
    )

    stats = load_team_stats(
        file_1,
        file_2,
    )

    assert stats.home_gf == 1.80
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40
    assert stats.away_ga == 1.30
    assert stats.home_xg == 1.75
    assert stats.home_xga == 1.05
    assert stats.away_xga == 1.25


def test_file_1_has_priority_over_file_2(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf,home_xg\n"
        "2.00,1.00,1.50,1.90\n",
    )

    create_csv(
        file_2,
        "home_gf,home_ga,away_gf,home_xg,away_ga\n"
        "1.00,2.00,0.50,1.10,1.40\n",
    )

    stats = load_team_stats(
        file_1,
        file_2,
    )

    assert stats.home_gf == 2.00
    assert stats.home_ga == 1.00
    assert stats.away_gf == 1.50
    assert stats.home_xg == 1.90
    assert stats.away_ga == 1.40


def test_loader_uses_selected_rows(tmp_path):
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
        "away_ga,home_xg\n"
        "1.10,1.20\n"
        "1.30,1.40\n",
    )

    stats = load_team_stats(
        file_1,
        file_2,
        row_index_1=1,
        row_index_2=1,
    )

    assert stats.home_gf == 2.00
    assert stats.home_ga == 3.00
    assert stats.away_gf == 4.00
    assert stats.away_ga == 1.30
    assert stats.home_xg == 1.40


def test_loader_accepts_mixed_csv_and_xlsx(tmp_path):
    openpyxl = pytest.importorskip(
        "openpyxl"
    )

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

    workbook.save(
        file_2
    )

    stats = load_team_stats(
        file_1,
        file_2,
    )

    assert stats.home_gf == 1.80
    assert stats.away_ga == 1.30
    assert stats.home_xg == 1.75
    assert stats.home_xga == 1.05
    assert stats.away_xga == 1.25


def test_loader_rejects_invalid_row_index(tmp_path):
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

    with pytest.raises(IndexError):
        load_team_stats(
            file_1,
            file_2,
            row_index_1=5,
        )


def test_loader_preserves_validation_rules(tmp_path):
    file_1 = tmp_path / "statistics_1.csv"
    file_2 = tmp_path / "statistics_2.csv"

    create_csv(
        file_1,
        "home_gf,home_ga,away_gf\n"
        "1.80,-1.10,1.40\n",
    )

    create_csv(
        file_2,
        "away_ga\n"
        "1.30\n",
    )

    with pytest.raises(ValueError):
        load_team_stats(
            file_1,
            file_2,
        )
