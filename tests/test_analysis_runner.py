"""
Q200 Engine - Analysis Runner Tests

Q200 V3.1
"""

from __future__ import annotations

import pytest

from q200_engine.analysis_runner import (
    RUNNER_VERSION,
    AnalysisRun,
    run_analysis,
    run_from_pipeline,
)

from q200_engine.pipeline import (
    Q200Pipeline,
)

from q200_engine.schema import (
    TeamStats,
)


def make_stats() -> TeamStats:
    """
    Q200 model test verisi.
    """

    return TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )


def make_odds() -> dict[str, float]:
    """
    Test için geçerli 1X2 odds.
    """

    return {
        "HOME": 2.10,
        "DRAW": 3.40,
        "AWAY": 3.80,
    }


def test_runner_version() -> None:
    assert (
        RUNNER_VERSION
        == "Q200-ANALYSIS-RUNNER-V1"
    )


def test_run_analysis_returns_analysis_run() -> None:
    result = run_analysis(
        stats=make_stats(),
        odds=make_odds(),
        bankroll=50_000,
    )

    assert isinstance(
        result,
        AnalysisRun,
    )

    assert result.result is not None

    assert (
        result.metadata["runner_version"]
        == RUNNER_VERSION
    )


def test_run_analysis_model_is_locked() -> None:
    result = run_analysis(
        stats=make_stats(),
        odds=make_odds(),
        bankroll=50_000,
    )

    assert (
        result.result.snapshot.locked
        is True
    )

    assert (
        result.metadata["model_locked"]
        is True
    )

    assert (
        result.metadata[
            "odds_used_after_model_lock"
        ]
        is True
    )


def test_odds_do_not_change_locked_model() -> None:
    stats = make_stats()

    pipeline = Q200Pipeline(
        stats
    )

    lambda_home_before = (
        pipeline.lambda_home
    )

    lambda_away_before = (
        pipeline.lambda_away
    )

    probabilities_before = (
        pipeline.probabilities
    )

    result = run_from_pipeline(
        pipeline=pipeline,
        odds=make_odds(),
        bankroll=50_000,
    )

    assert (
        result.result.snapshot.locked
        is True
    )

    assert (
        pipeline.lambda_home
        == lambda_home_before
    )

    assert (
        pipeline.lambda_away
        == lambda_away_before
    )

    assert (
        pipeline.probabilities
        == probabilities_before
    )


def test_run_from_existing_pipeline() -> None:
    pipeline = Q200Pipeline(
        make_stats()
    )

    result = run_from_pipeline(
        pipeline=pipeline,
        odds=make_odds(),
        bankroll=50_000,
    )

    assert isinstance(
        result,
        AnalysisRun,
    )

    assert (
        result.metadata[
            "existing_pipeline"
        ]
        is True
    )

    assert (
        result.result.snapshot
        == pipeline.snapshot
    )


def test_invalid_bankroll_is_rejected() -> None:
    with pytest.raises(ValueError):
        run_analysis(
            stats=make_stats(),
            odds=make_odds(),
            bankroll=0,
        )


def test_negative_bankroll_is_rejected() -> None:
    with pytest.raises(ValueError):
        run_analysis(
            stats=make_stats(),
            odds=make_odds(),
            bankroll=-100,
        )


def test_empty_odds_are_rejected() -> None:
    with pytest.raises(ValueError):
        run_analysis(
            stats=make_stats(),
            odds={},
            bankroll=50_000,
        )


def test_invalid_odds_are_rejected() -> None:
    with pytest.raises(ValueError):
        run_analysis(
            stats=make_stats(),
            odds={
                "HOME": 1.00,
                "DRAW": 3.40,
                "AWAY": 3.80,
            },
            bankroll=50_000,
        )


def test_non_dict_odds_are_rejected() -> None:
    with pytest.raises(TypeError):
        run_analysis(
            stats=make_stats(),
            odds=None,  # type: ignore[arg-type]
            bankroll=50_000,
        )


def test_invalid_stats_are_rejected() -> None:
    with pytest.raises(TypeError):
        run_analysis(
            stats=None,  # type: ignore[arg-type]
            odds=make_odds(),
            bankroll=50_000,
        )


def test_unlocked_pipeline_is_rejected() -> None:
    pipeline = Q200Pipeline(
        make_stats()
    )

    pipeline.snapshot.locked = False

    with pytest.raises(RuntimeError):
        run_from_pipeline(
            pipeline=pipeline,
            odds=make_odds(),
            bankroll=50_000,
        )
