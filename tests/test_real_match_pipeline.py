from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.real_match_pipeline import (
    REAL_MATCH_PIPELINE_VERSION,
    build_locked_model_from_soccerstats,
    run_real_match_from_pdfs,
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


def test_real_match_pipeline_version():
    assert (
        REAL_MATCH_PIPELINE_VERSION
        == "Q200-REAL-MATCH-PIPELINE-V1"
    )


def test_real_soccerstats_builds_locked_model():
    pipeline = (
        build_locked_model_from_soccerstats(
            STATISTICS_PDF
        )
    )

    assert pipeline.model_locked is True

    assert (
        pipeline.lambda_home
        == 1.50
    )

    assert (
        pipeline.lambda_away
        == 0.01
    )


def test_real_match_runs_from_statistics_and_odds_pdf():
    result = run_real_match_from_pdfs(
        STATISTICS_PDF,
        ODDS_PDF,
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert result.no_vig_probabilities
    assert result.fair_odds
    assert result.ev
    assert result.pessimistic_ev
    assert result.selections


def test_real_match_pipeline_rejects_unknown_market():
    with pytest.raises(KeyError):
        run_real_match_from_pdfs(
            STATISTICS_PDF,
            ODDS_PDF,
            market="UNKNOWN",
            bankroll=50_000,
            uncertainty="MEDIUM",
        )


def test_real_match_pipeline_rejects_invalid_bankroll():
    with pytest.raises(ValueError):
        run_real_match_from_pdfs(
            STATISTICS_PDF,
            ODDS_PDF,
            market="1X2",
            bankroll=0,
            uncertainty="MEDIUM",
        )
