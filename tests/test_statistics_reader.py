"""
Q200 Engine - Statistics Reader Tests

Q200 V3.1
"""

from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.statistics_reader import (
    read_csv,
    read_statistics_file,
    read_statistics_record,
)


# =========================================================
# CSV FIXTURE
# =========================================================

def create_csv(
    path: Path,
    content: str,
) -> None:

    path.write_text(
        content,
        encoding="utf-8",
    )


# =========================================================
# CSV READ
# =========================================================

def test_read_csv(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf,away_ga,"
            "home_xg,home_xga,away_xga,away_xg\n"
            "1.80,1.10,1.40,1.30,"
            "1.75,1.05,1.25,1.35\n"
        ),
    )

    rows = read_csv(
        file_path
    )

    assert len(rows) == 1

    assert rows[0]["home_gf"] == "1.80"
    assert rows[0]["away_xg"] == "1.35"


# =========================================================
# CSV HEADER NORMALIZATION
# =========================================================

def test_csv_headers_are_normalized(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            " HOME_GF , HOME_GA , Away_GF \n"
            "1.80,1.10,1.40\n"
        ),
    )

    rows = read_csv(
        file_path
    )

    assert rows[0]["home_gf"] == "1.80"
    assert rows[0]["home_ga"] == "1.10"
    assert rows[0]["away_gf"] == "1.40"


# =========================================================
# MULTIPLE ROWS
# =========================================================

def test_csv_reads_multiple_rows(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
            "2.00,0.90,1.60\n"
        ),
    )

    rows = read_csv(
        file_path
    )

    assert len(rows) == 2
    assert rows[0]["home_gf"] == "1.80"
    assert rows[1]["home_gf"] == "2.00"


# =========================================================
# EMPTY VALUES
# =========================================================

def test_empty_values_become_none(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf,home_xg\n"
            "1.80,1.10,1.40,\n"
        ),
    )

    rows = read_csv(
        file_path
    )

    assert rows[0]["home_xg"] is None


# =========================================================
# UNKNOWN COLUMN
# =========================================================

def test_unknown_column_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,unknown_column,away_gf\n"
            "1.80,10,1.40\n"
        ),
    )

    with pytest.raises(ValueError):

        read_csv(
            file_path
        )


# =========================================================
# DUPLICATE COLUMN
# =========================================================

def test_duplicate_column_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_gf,away_gf\n"
            "1.80,1.90,1.40\n"
        ),
    )

    with pytest.raises(ValueError):

        read_csv(
            file_path
        )


# =========================================================
# EMPTY CSV
# =========================================================

def test_empty_csv_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        "",
    )

    with pytest.raises(ValueError):

        read_csv(
            file_path
        )


# =========================================================
# MISSING FILE
# =========================================================

def test_missing_file_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "missing.csv"
    )

    with pytest.raises(
        FileNotFoundError
    ):

        read_statistics_file(
            file_path
        )


# =========================================================
# UNSUPPORTED EXTENSION
# =========================================================

def test_unsupported_extension_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.txt"
    )

    file_path.write_text(
        "test",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):

        read_statistics_file(
            file_path
        )


# =========================================================
# RECORD SELECTION
# =========================================================

def test_read_statistics_record(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
            "2.00,0.90,1.60\n"
        ),
    )

    record = read_statistics_record(
        file_path,
        row_index=1,
    )

    assert record["home_gf"] == "2.00"
    assert record["home_ga"] == "0.90"
    assert record["away_gf"] == "1.60"


# =========================================================
# INVALID ROW INDEX
# =========================================================

def test_invalid_row_index_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    with pytest.raises(IndexError):

        read_statistics_record(
            file_path,
            row_index=5,
        )


# =========================================================
# NEGATIVE ROW INDEX
# =========================================================

def test_negative_row_index_is_rejected(tmp_path):

    file_path = (
        tmp_path
        / "statistics.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    with pytest.raises(ValueError):

        read_statistics_record(
            file_path,
            row_index=-1,
        )


# =========================================================
# XLSX READER
# =========================================================

def test_xlsx_reader(tmp_path):

    openpyxl = pytest.importorskip(
        "openpyxl"
    )

    file_path = (
        tmp_path
        / "statistics.xlsx"
    )

    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    worksheet.append(
        [
            "home_gf",
            "home_ga",
            "away_gf",
            "away_ga",
        ]
    )

    worksheet.append(
        [
            1.80,
            1.10,
            1.40,
            1.30,
        ]
    )

    workbook.save(
        file_path
    )

    rows = read_statistics_file(
        file_path
    )

    assert len(rows) == 1
    assert rows[0]["home_gf"] == 1.80
    assert rows[0]["away_ga"] == 1.30


# =========================================================
# XLSX HEADER NORMALIZATION
# =========================================================

def test_xlsx_headers_are_normalized(tmp_path):

    openpyxl = pytest.importorskip(
        "openpyxl"
    )

    file_path = (
        tmp_path
        / "statistics.xlsx"
    )

    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    worksheet.append(
        [
            " HOME_GF ",
            "HOME_GA",
            "Away_GF",
        ]
    )

    worksheet.append(
        [
            1.80,
            1.10,
            1.40,
        ]
    )

    workbook.save(
        file_path
    )

    rows = read_statistics_file(
        file_path
    )

    assert rows[0]["home_gf"] == 1.80
    assert rows[0]["home_ga"] == 1.10
    assert rows[0]["away_gf"] == 1.40
