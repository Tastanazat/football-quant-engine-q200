from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.ingestion.models import OddsData
from q200_engine.odds_pdf_reader import (
    ODDS_PDF_READER_VERSION,
    extract_odds_pdf_text,
    odds_data_to_market,
    parse_odds_pdf,
    parse_odds_pdf_text,
)


REAL_ODDS_PDF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
)


SAMPLE_TEXT = """17 Eylül 2026 20:00
Real Betis - GetafeReal Betis - Getafe
Maç Sonucu
1 1.72 X 3.75 2 5.80
Maç Sonucu (2 Gol Farkta Erken Ödeme)
1 1.70 X 3.75 2 5.55
Çifte Şans
Toplam Goller
Üst 0.5 1.06 Alt 0.5 8.50
Üst 1.5 1.35 Alt 1.5 3.10
Üst 2.5 2.10 Alt 2.5 1.70
Karşılıklı Gol Olur
Evet 2.05 Hayır 1.69
Beraberlikte İade
Toplam Kornerler
Üst 9.5 1.95 Alt 9.5 1.80
Toplam Kornerler 3-Yönlü
"""


def test_reader_version() -> None:

    assert (
        ODDS_PDF_READER_VERSION
        == "Q200-ODDS-PDF-READER-V1"
    )


def test_parse_text_returns_odds_data() -> None:

    result = parse_odds_pdf_text(
        SAMPLE_TEXT
    )

    assert isinstance(
        result,
        OddsData,
    )

    assert result.match is not None

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )

    assert (
        result.match.date
        == "2026-09-17"
    )

    assert (
        result.match.time
        == "20:00"
    )

    assert result.markets["1X2"] == {
        "HOME": 1.72,
        "DRAW": 3.75,
        "AWAY": 5.80,
    }

    assert (
        result.markets[
            "TOTAL_GOALS_2.5"
        ]
        == {
            "OVER": 2.10,
            "UNDER": 1.70,
        }
    )

    assert result.markets["BTTS"] == {
        "YES": 2.05,
        "NO": 1.69,
    }

    assert (
        result.markets[
            "TOTAL_CORNERS_9.5"
        ]
        == {
            "OVER": 1.95,
            "UNDER": 1.80,
        }
    )


def test_odds_data_to_market() -> None:

    result = parse_odds_pdf_text(
        SAMPLE_TEXT
    )

    assert odds_data_to_market(
        result,
        "1X2",
    ) == {
        "HOME": 1.72,
        "DRAW": 3.75,
        "AWAY": 5.80,
    }


def test_unknown_market_is_rejected() -> None:

    result = parse_odds_pdf_text(
        SAMPLE_TEXT
    )

    with pytest.raises(KeyError):

        odds_data_to_market(
            result,
            "UNKNOWN",
        )


def test_invalid_input_is_rejected() -> None:

    with pytest.raises(TypeError):

        parse_odds_pdf_text(
            None
        )


def test_real_odds_pdf_fixture_exists() -> None:

    assert REAL_ODDS_PDF.is_file()

    assert (
        REAL_ODDS_PDF.stat().st_size
        > 0
    )


def test_real_odds_pdf_text_can_be_extracted() -> None:

    text = extract_odds_pdf_text(
        REAL_ODDS_PDF
    )

    assert (
        "Real Betis - Getafe"
        in text
    )

    assert (
        "Maç Sonucu"
        in text
    )

    assert (
        "Toplam Goller"
        in text
    )

    assert (
        "Karşılıklı Gol Olur"
        in text
    )


def test_real_odds_pdf_parses_match() -> None:

    result = parse_odds_pdf(
        REAL_ODDS_PDF
    )

    assert result.match is not None

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )

    assert (
        result.match.date
        == "2026-09-17"
    )

    assert (
        result.match.time
        == "20:00"
    )

    assert (
        result.match.source
        == "OddsPDF"
    )


def test_real_odds_pdf_parses_primary_markets() -> None:

    result = parse_odds_pdf(
        REAL_ODDS_PDF
    )

    assert result.markets["1X2"] == {
        "HOME": 1.72,
        "DRAW": 3.75,
        "AWAY": 5.80,
    }

    assert (
        result.markets[
            "TOTAL_GOALS_2.5"
        ]
        == {
            "OVER": 2.10,
            "UNDER": 1.70,
        }
    )

    assert result.markets["BTTS"] == {
        "YES": 2.05,
        "NO": 1.69,
    }

    assert (
        result.markets[
            "TOTAL_CORNERS_9.5"
        ]
        == {
            "OVER": 1.95,
            "UNDER": 1.80,
        }
    )
