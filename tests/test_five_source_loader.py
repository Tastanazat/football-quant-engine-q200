from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.five_source_loader import (
    FIVE_SOURCE_LOADER_VERSION,
    load_ppi_pdf,
    load_statshub_text,
)
from q200_engine.ingestion.models import (
    MatchInfo,
)


PPI_PDF = (
    Path(__file__).resolve().parent.parent
    / "WEB_1789630147.pdf"
)


STATSHUB_TEXT = """
Goals 3.05 1.70 1.35 2 3 1 2 1 1 2 1 2
Corners 9.15 4.30 4.85 4 5 6 8 2 4 4 4 8
Expected Goals (xG) 2.92 1.50 1.41 3.75 1.80 0.93 1.92 0.71 1.24 1.51 0.97 1.80
Total Shots 26.50 15.05 11.45 26 20 10 20 15 18 18 7 16
Possession 100.00 50.85 49.15 38 55 42 60 58 48 64 37 45
"""


def make_match() -> MatchInfo:
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="2026-09-17",
        time="20:00",
        competition="Spain - LaLiga",
        source="Q200",
    )


def test_loader_version() -> None:

    assert (
        FIVE_SOURCE_LOADER_VERSION
        == "Q200-FIVE-SOURCE-LOADER-V1"
    )


def test_statshub_text_loader() -> None:

    result = load_statshub_text(
        STATSHUB_TEXT,
        match=make_match(),
    )

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )

    assert (
        result.values["goals_avg"]
        == 3.05
    )

    assert (
        result.values["goals_for"]
        == 1.70
    )

    assert (
        result.values["goals_agt"]
        == 1.35
    )

    assert (
        result.values["xg_avg"]
        == 2.92
    )


def test_statshub_text_empty_is_rejected() -> None:

    with pytest.raises(
        ValueError,
        match="boş olamaz",
    ):
        load_statshub_text(
            "",
            match=make_match(),
        )


def test_ppi_pdf_fixture_exists() -> None:

    assert PPI_PDF.exists()
    assert PPI_PDF.is_file()


def test_ppi_pdf_loader_reads_real_source() -> None:

    result = load_ppi_pdf(
        PPI_PDF,
        match=make_match(),
    )

    assert result.home_ppg == 2.40
    assert result.home_opponent_ppg == 0.97
    assert result.home_ppi == 2.33

    assert result.away_ppg == 1.00
    assert result.away_opponent_ppg == 1.25
    assert result.away_ppi == 1.25


def test_ppi_pdf_loader_preserves_match_identity() -> None:

    result = load_ppi_pdf(
        PPI_PDF,
        match=make_match(),
    )

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )


def test_ppi_pdf_missing_file_is_rejected() -> None:

    with pytest.raises(
        FileNotFoundError,
    ):
        load_ppi_pdf(
            "missing-ppi.pdf",
            match=make_match(),
        )
