"""
Q200 Engine - Five Source Runner Tests

Q200 V3.1

Five Source Runner:

    StatsHub HOME
    StatsHub AWAY
    SoccerSTATS
    PPI
    Odds
        ↓
    Five Source Analysis
"""

from __future__ import annotations

from pathlib import Path

from q200_engine.five_source_runner import (
    FIVE_SOURCE_RUNNER_VERSION,
    run_five_source_files,
)
from q200_engine.ingestion.models import (
    MatchInfo,
)


SOCCERSTATS_PDF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "soccerstats"
    / "WEB_1789630115.pdf"
)

PPI_PDF = (
    Path(__file__).resolve().parent.parent
    / "WEB_1789630147.pdf"
)

ODDS_PDF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
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


def test_runner_version() -> None:
    assert (
        FIVE_SOURCE_RUNNER_VERSION
        == "Q200-FIVE-SOURCE-RUNNER-V1"
    )


def test_required_real_source_files_exist() -> None:
    assert SOCCERSTATS_PDF.exists()
    assert SOCCERSTATS_PDF.is_file()

    assert PPI_PDF.exists()
    assert PPI_PDF.is_file()

    assert ODDS_PDF.exists()
    assert ODDS_PDF.is_file()


def test_runner_reaches_locked_q200_analysis(
    tmp_path,
    monkeypatch,
) -> None:
    """
    Runner'ın bütün kaynakları hazırlayıp mevcut
    Five Source Pipeline'a ulaştırdığını doğrular.

    Gerçek StatsHub görüntüsü olmadığı için
    loader'ın image fonksiyonu kontrollü şekilde
    gerçek StatsHubData üretir.

    Diğer PDF kaynakları gerçek fixture'lardır.
    """

    from q200_engine.five_source_runner import (
        StatsHubData,
    )

    match = make_match()

    home_data = StatsHubData(
        match=match,
        values={
            "goals_for": 1.70,
            "goals_agt": 1.35,
            "xg_avg": 2.92,
        },
        raw_text=STATSHUB_TEXT,
        source_metadata={
            "source": "StatsHub HOME",
            "approved": True,
        },
    )

    away_data = StatsHubData(
        match=match,
        values={
            "goals_for": 1.70,
            "goals_agt": 1.35,
            "xg_avg": 2.92,
        },
        raw_text=STATSHUB_TEXT,
        source_metadata={
            "source": "StatsHub AWAY",
            "approved": True,
        },
    )

    calls = []

    def fake_statshub_loader(
        image_path,
        *,
        match,
        ocr_text=None,
        ocr_engine=None,
    ):
        calls.append(
            (
                str(image_path),
                ocr_text,
            )
        )

        if "home" in str(image_path).lower():
            return home_data

        return away_data

    monkeypatch.setattr(
        "q200_engine.five_source_runner.load_statshub_image",
        fake_statshub_loader,
    )

    home_image = (
        tmp_path / "statshub_home.jpg"
    )

    away_image = (
        tmp_path / "statshub_away.jpg"
    )

    home_image.write_bytes(
        b"fake-home-image"
    )

    away_image.write_bytes(
        b"fake-away-image"
    )

    result = run_five_source_files(
        match=match,
        statshub_home_image=home_image,
        statshub_away_image=away_image,
        soccerstats_pdf=SOCCERSTATS_PDF,
        ppi_pdf=PPI_PDF,
        odds_pdf=ODDS_PDF,
        bankroll=50_000,
        market="1X2",
        uncertainty="MEDIUM",
        home_ocr_text=STATSHUB_TEXT,
        away_ocr_text=STATSHUB_TEXT,
    )

    assert len(calls) == 2

    assert result is not None

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert result.snapshot.probabilities

    assert result.fair_odds

    assert result.no_vig_probabilities

    assert result.ev

    assert result.pessimistic_probabilities

    assert result.pessimistic_ev

    assert isinstance(
        result.selections,
        list,
    )


def test_runner_rejects_invalid_match() -> None:
    try:
        run_five_source_files(
            match="invalid",
            statshub_home_image="home.jpg",
            statshub_away_image="away.jpg",
            soccerstats_pdf=SOCCERSTATS_PDF,
            ppi_pdf=PPI_PDF,
            odds_pdf=ODDS_PDF,
            bankroll=50_000,
        )
    except TypeError as exc:
        assert (
            "MatchInfo"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Geçersiz MatchInfo kabul edildi."
        )
