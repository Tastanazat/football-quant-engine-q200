"""
Q200 Engine - Evaluation Integration Test

Q200 V3.1

Amaç
-----
Mevcut History, Settlement, Performance,
Calibration ve Evaluation katmanlarının tek
bir zincir halinde çalıştığını doğrulamak.

Akış:

AnalysisResult
    ↓
History.save()
    ↓
History.record_result()
    ↓
History.settle_record()
    ↓
build_evaluation()
    ↓
Performance + Calibration
"""

from __future__ import annotations

from pathlib import Path

from q200_engine.evaluation import (
    EvaluationReport,
    build_evaluation,
)
from q200_engine.history import (
    AnalysisHistory,
)
from q200_engine.pipeline import (
    Q200Pipeline,
)
from q200_engine.schema import (
    TeamStats,
)


def make_stats() -> TeamStats:
    """
    Q200 model testi için kontrollü TeamStats.
    """

    return TeamStats(
        home_gf=2.0,
        away_gf=1.2,
        home_ga=1.5,
        away_ga=1.8,
        home_xg=1.7,
        away_xg=1.1,
        home_xga=1.4,
        away_xga=1.0,
    )


def make_result():
    """
    Gerçek Q200Pipeline üzerinden locked AnalysisResult üretir.
    """

    pipeline = Q200Pipeline(
        make_stats()
    )

    assert pipeline.model_locked is True

    result = pipeline.analyze_odds(
        odds={
            "HOME": 1.80,
            "DRAW": 3.50,
            "AWAY": 4.50,
        },
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    return result


def test_history_settlement_to_evaluation_chain(
    tmp_path: Path,
):
    """
    AnalysisResult → History → Result →
    Settlement → Evaluation zincirini doğrular.
    """

    result = make_result()

    history = AnalysisHistory(
        tmp_path
        / "evaluation.sqlite"
    )

    record_id = history.save(
        result,
        "INTEGRATION-MATCH-001",
    )

    assert record_id == 1

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["result_recorded"]
        is False
    )

    assert (
        record["settlement_recorded"]
        is False
    )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    recorded = history.record_result(
        record_id,
        2,
        1,
    )

    assert recorded is True

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["result_recorded"]
        is True
    )

    assert (
        record["home_goals"]
        == 2
    )

    assert (
        record["away_goals"]
        == 1
    )

    # -----------------------------------------------------
    # SETTLEMENT
    # -----------------------------------------------------

    settlement = history.settle_record(
        record_id
    )

    assert isinstance(
        settlement,
        dict,
    )

    assert (
        settlement["record_id"]
        == record_id
    )

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["settlement_recorded"]
        is True
    )

    assert (
        record["settlement"]
        is not None
    )

    # -----------------------------------------------------
    # EVALUATION
    # -----------------------------------------------------

    evaluation = build_evaluation(
        history,
        starting_bankroll=50_000,
        bucket_count=10,
    )

    assert isinstance(
        evaluation,
        EvaluationReport,
    )

    assert (
        evaluation.evaluation_version
        == "Q200-EVALUATION-V1"
    )

    # -----------------------------------------------------
    # PERFORMANCE
    # -----------------------------------------------------

    performance = (
        evaluation.performance
    )

    assert (
        performance.total_analysis_records
        == 1
    )

    assert (
        performance.completed_matches
        == 1
    )

    assert (
        performance.settled_matches
        == 1
    )

    # -----------------------------------------------------
    # CALIBRATION
    # -----------------------------------------------------

    calibration = (
        evaluation.calibration
    )

    assert (
        calibration.total_predictions
        >= 0
    )

    assert (
        calibration.evaluated_predictions
        >= 0
    )

    assert (
        calibration.coverage
        >= 0.0
    )

    assert (
        calibration.coverage
        <= 1.0
    )

    # -----------------------------------------------------
    # MARKET LAYERS
    # -----------------------------------------------------

    assert isinstance(
        evaluation.market_performance,
        dict,
    )

    assert isinstance(
        evaluation.market_calibration,
        dict,
    )

    assert isinstance(
        evaluation.calibration_buckets,
        list,
    )


def test_evaluation_does_not_modify_history(
    tmp_path: Path,
):
    """
    Evaluation salt-okunur olmalıdır.

    Evaluation çalışmadan önceki History
    kayıt sayısı ile sonraki aynı kalmalıdır.
    """

    result = make_result()

    history = AnalysisHistory(
        tmp_path
        / "evaluation-readonly.sqlite"
    )

    record_id = history.save(
        result,
        "INTEGRATION-READONLY-001",
    )

    history.record_result(
        record_id,
        1,
        0,
    )

    history.settle_record(
        record_id
    )

    before_count = history.count()

    before_record = history.get(
        record_id
    )

    assert before_record is not None

    evaluation = build_evaluation(
        history
    )

    assert isinstance(
        evaluation,
        EvaluationReport,
    )

    after_count = history.count()

    after_record = history.get(
        record_id
    )

    assert after_record is not None

    assert (
        after_count
        == before_count
    )

    assert (
        after_record
        == before_record
    )


def test_evaluation_contains_calibration_buckets(
    tmp_path: Path,
):
    """
    Evaluation çıktısının calibration bucket
    katmanını taşıdığını doğrular.
    """

    result = make_result()

    history = AnalysisHistory(
        tmp_path
        / "evaluation-buckets.sqlite"
    )

    record_id = history.save(
        result,
        "INTEGRATION-BUCKETS-001",
    )

    history.record_result(
        record_id,
        2,
        1,
    )

    history.settle_record(
        record_id
    )

    evaluation = build_evaluation(
        history,
        bucket_count=10,
    )

    assert isinstance(
        evaluation.calibration_buckets,
        list,
    )

    for bucket in (
        evaluation.calibration_buckets
    ):
        assert (
            0.0
            <= bucket.lower_bound
            <= 1.0
        )

        assert (
            0.0
            <= bucket.upper_bound
            <= 1.0
        )

        assert (
            bucket.lower_bound
            <= bucket.upper_bound
        )

        assert (
            bucket.predictions
            >= 0
        )

        assert (
            bucket.wins
            >= 0
        )
