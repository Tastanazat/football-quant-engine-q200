from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.ingestion.models import SoccerStatsData
from q200_engine.ingestion.soccerstats_parser import (
    SOCCERSTATS_PARSER_VERSION,
    extract_pdf_text,
    parse_soccerstats_pdf,
)


PDF_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "WEB_1789630115.pdf"
)


def test_real_soccerstats_pdf_fixture_exists():
    assert PDF_PATH.exists()
    assert PDF_PATH.is_file()
    assert PDF_PATH.stat().st_size > 0


def test_real_soccerstats_pdf_text_can_be_extracted():
    text = extract_pdf_text(PDF_PATH)

    assert isinstance(text, str)
    assert len(text) > 1000

    normalized = text.lower()

    assert "real betis" in normalized
    assert "getafe" in normalized


def test_real_soccerstats_pdf_contains_match_information():
    text = extract_pdf_text(PDF_PATH)

    normalized = text.lower()

    assert "real betis vs getafe" in normalized
    assert "17 sep" in normalized


def test_real_soccerstats_pdf_contains_goal_statistics():
    text = extract_pdf_text(PDF_PATH)

    normalized = text.lower()

    assert "goal statistics" in normalized
    assert "goals scored" in normalized
    assert "goals conceded" in normalized


def test_real_soccerstats_pdf_contains_corner_statistics():
    text = extract_pdf_text(PDF_PATH)

    normalized = text.lower()

    assert "corner statistics" in normalized
    assert "avg corners for" in normalized
    assert "avg corners against" in normalized


def test_real_soccerstats_pdf_contains_h2h_statistics():
    text = extract_pdf_text(PDF_PATH)

    normalized = text.lower()

    assert "head-to-head results" in normalized
    assert "h2h stats" in normalized


def test_real_soccerstats_pdf_parser_returns_soccerstats_data():
    result = parse_soccerstats_pdf(PDF_PATH)

    assert isinstance(
        result,
        SoccerStatsData,
    )


def test_real_soccerstats_pdf_parser_returns_populated_data():
    result = parse_soccerstats_pdf(PDF_PATH)

    assert isinstance(
        result,
        SoccerStatsData,
    )

    # Parser'ın gerçek PDF'den boş bir nesne üretmesini engeller.
    data = vars(result)

    assert data


def test_real_soccerstats_pdf_parser_preserves_real_team_names():
    result = parse_soccerstats_pdf(PDF_PATH)

    data = vars(result)

    serialized = str(data).lower()

    assert "real betis" in serialized
    assert "getafe" in serialized


def test_real_soccerstats_pdf_parser_version():
    assert isinstance(
        SOCCERSTATS_PARSER_VERSION,
        str,
    )

    assert (
        SOCCERSTATS_PARSER_VERSION
    )


def test_real_soccerstats_pdf_is_not_empty_after_parsing():
    result = parse_soccerstats_pdf(PDF_PATH)

    data = vars(result)

    non_empty_values = [
        value
        for value in data.values()
        if value is not None
    ]

    assert non_empty_values


@pytest.mark.parametrize(
    "required_text",
    [
        "Real Betis",
        "Getafe",
        "Corner statistics",
        "Head-to-Head results",
    ],
)
def test_real_soccerstats_pdf_required_sections(
    required_text: str,
):
    text = extract_pdf_text(PDF_PATH)

    assert required_text.lower() in text.lower()
