from __future__ import annotations

from pathlib import Path

from q200_engine.pdf_pipeline import (
    PDF_PIPELINE_VERSION,
    run_pipeline_from_pdf_sources,
)


SOCCERSTATS_PDF = (
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


def test_pdf_pipeline_version() -> None:
    assert (
        PDF_PIPELINE_VERSION
        == "Q200-PDF-PIPELINE-V1"
    )


def test_real_pdf_pipeline_files_exist() -> None:
    assert SOCCERSTATS_PDF.exists()
    assert SOCCERSTATS_PDF.is_file()

    assert ODDS_PDF.exists()
    assert ODDS_PDF.is_file()


def test_real_pdf_pipeline_runs_q200() -> None:
    result = run_pipeline_from_pdf_sources(
        statistics_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert (
        result.snapshot.lambda_home
        > 0
    )

    assert (
        result.snapshot.lambda_away
        > 0
    )


def test_real_pdf_pipeline_contains_odds_analysis() -> None:
    result = run_pipeline_from_pdf_sources(
        statistics_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.no_vig_probabilities
    assert result.fair_odds
    assert result.ev
    assert result.pessimistic_probabilities
    assert result.pessimistic_ev
    assert result.selections


def test_real_pdf_pipeline_preserves_model_lock() -> None:
    result = run_pipeline_from_pdf_sources(
        statistics_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert (
        result.snapshot.lambda_home
        > 0
    )

    assert (
        result.snapshot.lambda_away
        > 0
    )


def test_real_pdf_pipeline_produces_1x2_outcomes() -> None:
    result = run_pipeline_from_pdf_sources(
        statistics_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    outcomes = {
        selection["outcome"]
        for selection in result.selections
    }

    assert "HOME" in outcomes
    assert "DRAW" in outcomes
    assert "AWAY" in outcomes
