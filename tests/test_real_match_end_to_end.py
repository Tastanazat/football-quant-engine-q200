from __future__ import annotations

from pathlib import Path

from q200_engine.file_pipeline import (
    run_pipeline_from_sources,
)
from q200_engine.ingestion.canonical_adapter import (
    validated_canonical_to_team_stats,
)
from q200_engine.ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)
from q200_engine.ingestion.validated_pipeline import (
    map_and_validate,
)
from q200_engine.model import calculate_lambdas
from q200_engine.odds_pdf_reader import (
    odds_data_to_market,
    parse_odds_pdf,
)


STATISTICS_PDF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "soccerstats"
    / "WEB_1789630115.pdf"
)


ODDS_PDF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
)


def test_real_match_fixture_files_exist() -> None:
    assert STATISTICS_PDF.exists()
    assert STATISTICS_PDF.is_file()

    assert ODDS_PDF.exists()
    assert ODDS_PDF.is_file()


def test_real_soccerstats_reaches_q200_model() -> None:
    soccerstats = parse_soccerstats_pdf(
        STATISTICS_PDF
    )

    assert soccerstats.match.home_team == (
        "Real Betis"
    )

    assert soccerstats.match.away_team == (
        "Getafe"
    )

    validated = map_and_validate(
        soccerstats=soccerstats
    )

    assert validated.valid is True
    assert validated.validation.issues == []

    stats = validated_canonical_to_team_stats(
        validated
    )

    assert stats.home_gf == 1.00
    assert stats.home_ga == 0.00
    assert stats.away_gf == 0.00
    assert stats.away_ga == 2.00

    lambda_home, lambda_away = (
        calculate_lambdas(stats)
    )

    assert lambda_home == 1.50
    assert lambda_away == 0.01


def test_real_odds_pdf_reaches_odds_layer() -> None:
    odds_data = parse_odds_pdf(
        ODDS_PDF
    )

    assert odds_data.match is not None

    assert odds_data.match.home_team == (
        "Real Betis"
    )

    assert odds_data.match.away_team == (
        "Getafe"
    )

    odds = odds_data_to_market(
        odds_data,
        "1X2",
    )

    assert odds == {
        "HOME": 1.72,
        "DRAW": 3.75,
        "AWAY": 5.80,
    }


def test_real_match_statistics_and_odds_reach_q200() -> None:
    soccerstats = parse_soccerstats_pdf(
        STATISTICS_PDF
    )

    odds_data = parse_odds_pdf(
        ODDS_PDF
    )

    odds = odds_data_to_market(
        odds_data,
        "1X2",
    )

    result = run_pipeline_from_sources(
        soccerstats=soccerstats,
        odds=odds,
        bankroll=50_000.0,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert result.snapshot.lambda_home == 1.50
    assert result.snapshot.lambda_away == 0.01

    assert result.no_vig_probabilities
    assert result.fair_odds
    assert result.ev
    assert result.pessimistic_probabilities
    assert result.pessimistic_ev
    assert result.selections


def test_odds_are_processed_after_model_lock() -> None:
    soccerstats = parse_soccerstats_pdf(
        STATISTICS_PDF
    )

    validated = map_and_validate(
        soccerstats=soccerstats
    )

    stats = validated_canonical_to_team_stats(
        validated
    )

    from q200_engine.pipeline import Q200Pipeline

    pipeline = Q200Pipeline(
        stats
    )

    assert pipeline.model_locked is True
    assert pipeline.lambda_home == 1.50
    assert pipeline.lambda_away == 0.01

    odds_data = parse_odds_pdf(
        ODDS_PDF
    )

    odds = odds_data_to_market(
        odds_data,
        "1X2",
    )

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=50_000.0,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.lambda_home
        == 1.50
    )

    assert (
        result.snapshot.lambda_away
        == 0.01
    )
