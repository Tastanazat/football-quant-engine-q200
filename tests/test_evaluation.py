from __future__ import annotations

import json
import math

import pytest

from q200_engine.evaluation import (
    EVALUATION_VERSION,
    EvaluationReport,
    build_evaluation,
    evaluation_to_dict,
    evaluation_to_json,
    evaluation_to_text,
)


class FakeHistory:

    def __init__(
        self,
        records,
    ):
        self.records = records

    def count(
        self,
    ):
        return len(
            self.records
        )

    def count_completed(
        self,
    ):
        return sum(
            1
            for record in self.records
            if record.get(
                "result_recorded"
            ) is True
        )

    def list(
        self,
        limit=50,
    ):
        return self.records[
            :limit
        ]

    def get(
        self,
        record_id,
    ):
        for record in self.records:
            if record["id"] == record_id:
                return record

        return None


def selection(
    outcome,
    settlement,
    stake=100.0,
    profit=None,
):
    if profit is None:
        if settlement == "WIN":
            profit = stake
        elif settlement == "LOSS":
            profit = -stake
        else:
            profit = 0.0

    return {
        "outcome": outcome,
        "odds": 2.0,
        "stake": stake,
        "settlement": settlement,
        "profit": profit,
    }


def record(
    record_id,
    selections,
    probabilities,
    *,
    settled=True,
):
    return {
        "id": record_id,

        "match_id": (
            f"M-{record_id}"
        ),

        "result_recorded": (
            settled
        ),

        "settlement_recorded": (
            settled
        ),

        "settlement": (
            {
                "selections": selections
            }
            if settled
            else None
        ),

        "report": {
            "model": {
                "probabilities": (
                    probabilities
                ),
            },

            "stress_test": {
                "probabilities": {
                    "BASELINE": (
                        probabilities
                    ),
                }
            },
        },
    }


def test_evaluation_version():

    assert (
        EVALUATION_VERSION
        == "Q200-EVALUATION-V1"
    )


def test_build_evaluation_combines_performance_and_calibration():

    history = FakeHistory(
        [
            record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                        100.0,
                        100.0,
                    ),

                    selection(
                        "OVER_2.5",
                        "LOSS",
                        50.0,
                        -50.0,
                    ),
                ],
                {
                    "HOME": 0.75,
                    "OVER_2.5": 0.40,
                },
            )
        ]
    )

    evaluation = build_evaluation(
        history,
        starting_bankroll=1000.0,
    )

    assert isinstance(
        evaluation,
        EvaluationReport,
    )

    assert (
        evaluation.evaluation_version
        == EVALUATION_VERSION
    )

    assert (
        evaluation.performance.total_bets
        == 2
    )

    assert (
        evaluation.performance.total_profit
        == 50.0
    )

    assert math.isclose(
        evaluation.performance.roi,
        50.0 / 150.0,
    )

    assert (
        evaluation.calibration
        .evaluated_predictions
        == 2
    )

    assert (
        "HOME"
        in evaluation.market_performance
    )

    assert (
        "OVER_2.5"
        in evaluation.market_calibration
    )

    assert (
        len(
            evaluation.calibration_buckets
        )
        == 10
    )


def test_evaluation_ignores_unsettled_history():

    history = FakeHistory(
        [
            record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    )
                ],
                {
                    "HOME": 0.80
                },
                settled=False,
            )
        ]
    )

    evaluation = build_evaluation(
        history
    )

    assert (
        evaluation.performance.total_bets
        == 0
    )

    assert (
        evaluation.calibration
        .evaluated_predictions
        == 0
    )

    assert (
        evaluation.market_performance
        == {}
    )

    assert (
        evaluation.market_calibration
        == {}
    )


def test_evaluation_dict_is_serializable():

    history = FakeHistory(
        [
            record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    )
                ],
                {
                    "HOME": 0.80
                },
            )
        ]
    )

    evaluation = build_evaluation(
        history
    )

    payload = evaluation_to_dict(
        evaluation
    )

    assert (
        payload["evaluation_version"]
        == EVALUATION_VERSION
    )

    assert (
        payload["performance"]
        ["total_bets"]
        == 1
    )

    assert (
        payload["calibration"]
        ["evaluated_predictions"]
        == 1
    )

    json.dumps(
        payload
    )


def test_evaluation_json():

    evaluation = build_evaluation(
        FakeHistory([])
    )

    output = evaluation_to_json(
        evaluation,
        indent=2,
    )

    parsed = json.loads(
        output
    )

    assert (
        parsed["evaluation_version"]
        == EVALUATION_VERSION
    )

    assert (
        parsed["performance"]
        ["total_bets"]
        == 0
    )


def test_evaluation_json_indent_validation():

    evaluation = build_evaluation(
        FakeHistory([])
    )

    with pytest.raises(
        TypeError
    ):

        evaluation_to_json(
            evaluation,
            indent=True,
        )

    with pytest.raises(
        ValueError
    ):

        evaluation_to_json(
            evaluation,
            indent=-1,
        )


def test_evaluation_text_contains_main_sections():

    evaluation = build_evaluation(
        FakeHistory([])
    )

    text = evaluation_to_text(
        evaluation
    )

    assert (
        "Q200 V3.1 EVALUATION RAPORU"
        in text
    )

    assert (
        "PERFORMANCE"
        in text
    )

    assert (
        "CALIBRATION"
        in text
    )

    assert (
        "Brier Score"
        in text
    )

    assert (
        "Log Loss"
        in text
    )


def test_evaluation_text_rejects_invalid_input():

    with pytest.raises(
        TypeError
    ):

        evaluation_to_text(
            None
        )


def test_evaluation_dict_rejects_invalid_input():

    with pytest.raises(
        TypeError
    ):

        evaluation_to_dict(
            None
        )
