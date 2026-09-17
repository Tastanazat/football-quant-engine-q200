from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.odds_pdf_reader import (
    ODDS_PDF_READER_VERSION,
    odds_data_to_market,
    parse_odds_pdf,
    parse_odds_pdf_text,
)


PDF_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
)


SAMPLE_TEXT = """17 Eylül 2026 20:00
Real Betis - Getafe

Maç Sonucu
1 1.72 X 3.75 2 5.80

Maç Sonucu (2 Gol Farkta Erken Ödeme)
1 1.70 X 3.75 2 5.55

Çifte Şans
1X 1.16 12 1.30 X2 2.30

Toplam Goller
Üst 0.5 1.06 Alt 0.5 8.50
Üst 1.5 1.35 Alt 1.5 3.10
Üst 2.5 2.10 Alt 2.5 1.70

Karşılıklı Gol Olur
Evet 2.05 Hayır 1.69

Toplam Kornerler
Üst 9.5 1.95 Alt 9.5 1.80

Toplam Kornerler 3-Yönlü
"""


def test_odds_pdf_reader_version():
    assert (
        ODDS_PDF_READER_VERSION
        == "Q200-ODDS-PDF-READER-V1"
    )


def test_parse_odds_pdf_text():
    result = parse_odds_pdf_text(
        SAMPLE_TEXT
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


def test_odds_data_to_market():
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


def test_unknown_market_is_rejected():
    result = parse_odds_pdf_text(
        SAMPLE_TEXT
    )

    with pytest.raises(KeyError):
        odds_data_to_market(
            result,
            "UNKNOWN",
        )


def test_real_odds_pdf_exists():
    assert PDF_PATH.exists()
    assert PDF_PATH.is_file()
    assert PDF_PATH.stat().st_size > 0


def test_real_odds_pdf_parses_match():
    result = parse_odds_pdf(
        PDF_PATH
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
        result.match.date
        == "2026-09-17"
    )

    assert (
        result.match.time
        == "20:00"
    )


def test_real_odds_pdf_parses_primary_markets():
    result = parse_odds_pdf(
        PDF_PATH
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
