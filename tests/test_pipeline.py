import pytest

from q200_engine.schema import TeamStats
from q200_engine.pipeline import Q200Pipeline, run_pipeline


def test_pipeline_creates_locked_model():
    stats = TeamStats(2, 1, 1)

    pipeline = Q200Pipeline(stats)

    assert pipeline.model_locked is True
    assert pipeline.snapshot.locked is True


def test_pipeline_exposes_lambdas():
    stats = TeamStats(2, 1, 1)

    pipeline = Q200Pipeline(stats)

    assert pipeline.lambda_home == pipeline.snapshot.lambda_home
    assert pipeline.lambda_away == pipeline.snapshot.lambda_away


def test_pipeline_returns_analysis_result():
    stats = TeamStats(2, 1, 1)

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True
    assert isinstance(result.fair_odds, dict)
    assert isinstance(result.no_vig_probabilities, dict)
    assert isinstance(result.ev, dict)
    assert isinstance(result.selections, list)


def test_pipeline_does_not_modify_model():
    stats = TeamStats(
        2,
        1,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    before = pipeline.snapshot

    pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    after = pipeline.snapshot

    assert before == after


def test_pipeline_rejects_invalid_bankroll():
    stats = TeamStats(2, 1, 1)

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):
        pipeline.analyze_odds(
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            bankroll=0,
        )


def test_pipeline_rejects_invalid_odds():
    stats = TeamStats(2, 1, 1)

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):
        pipeline.analyze_odds(
            {
                "HOME": 1.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            bankroll=50_000,
        )


def test_run_pipeline():
    stats = TeamStats(2, 1, 1)

    result = run_pipeline(
        stats,
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True
