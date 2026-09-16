from __future__ import annotations

import math

import pytest

from q200_engine.calibration import (
    CALIBRATION_VERSION,
    calibration_buckets,
    calibration_by_market,
    calibration_summary,
    collect_observations,
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

            if (
                record["id"]
                == record_id
            ):

                return record

        return None


def make_record(
    record_id,
    selections,
    *,
    settled=True,
):

    return {
        "id": record_id,

        "match_id": (
            f"M-{record_id}"
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
    }


def selection(
    outcome,
    settlement,
):

    return {
        "outcome": outcome,

        "odds": 2.0,

        "stake": 100.0,

        "settlement": settlement,

        "profit": (
            100.0
            if settlement == "WIN"
            else -100.0
        ),
    }


def add_report(
    record,
    baseline,
    model=None,
):

    record["report"] = {
        "model": {
            "probabilities": (
                model or {}
            ),
        },

        "stress_test": {
            "probabilities": {
                "BASELINE": baseline,
            }
        },
    }

    return record


def test_version():

    assert (
        CALIBRATION_VERSION
        == "Q200-CALIBRATION-V1"
    )


def test_collect_observations_uses_baseline_probabilities():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    ),
                    selection(
                        "DRAW",
                        "LOSS",
                    ),
                    selection(
                        "AWAY",
                        "VOID",
                    ),
                ],
            ),
            {
                "HOME": 0.70,
                "DRAW": 0.20,
            },
            {
                "HOME": 0.60,
                "DRAW": 0.30,
            },
        )
    ]

    (
        observations,
        voids,
        missing,
    ) = collect_observations(
        FakeHistory(records)
    )

    assert len(
        observations
    ) == 2

    assert voids == 1

    assert missing == 0

    assert (
        observations[0].market
        == "HOME"
    )

    assert (
        observations[0]
        .predicted_probability
        == 0.70
    )

    assert (
        observations[0].actual
        == 1
    )

    assert (
        observations[1].market
        == "DRAW"
    )

    assert (
        observations[1]
        .predicted_probability
        == 0.20
    )

    assert (
        observations[1].actual
        == 0
    )


def test_collect_observations_falls_back_to_model_probability():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    )
                ],
            ),
            {},
            {
                "HOME": 0.75
            },
        )
    ]

    (
        observations,
        voids,
        missing,
    ) = collect_observations(
        FakeHistory(records)
    )

    assert len(
        observations
    ) == 1

    assert (
        observations[0]
        .predicted_probability
        == 0.75
    )

    assert voids == 0

    assert missing == 0


def test_missing_probability_is_counted():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "UNKNOWN_MARKET",
                        "WIN",
                    )
                ],
            ),
            {},
            {},
        )
    ]

    (
        observations,
        voids,
        missing,
    ) = collect_observations(
        FakeHistory(records)
    )

    assert observations == []

    assert voids == 0

    assert missing == 1


def test_unsettled_records_are_ignored():

    record = add_report(
        make_record(
            1,
            [
                selection(
                    "HOME",
                    "WIN",
                )
            ],
            settled=False,
        ),
        {
            "HOME": 0.90
        },
    )

    (
        observations,
        voids,
        missing,
    ) = collect_observations(
        FakeHistory(
            [record]
        )
    )

    assert observations == []

    assert voids == 0

    assert missing == 0


def test_calibration_summary():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    ),
                    selection(
                        "DRAW",
                        "LOSS",
                    ),
                ],
            ),
            {
                "HOME": 0.80,
                "DRAW": 0.30,
            },
        )
    ]

    summary = calibration_summary(
        FakeHistory(records)
    )

    assert (
        summary.total_predictions
        == 2
    )

    assert (
        summary.evaluated_predictions
        == 2
    )

    assert (
        summary.void_predictions
        == 0
    )

    assert (
        summary.missing_probability_predictions
        == 0
    )

    expected_brier = (
        (0.80 - 1.0) ** 2
        + (0.30 - 0.0) ** 2
    ) / 2

    assert math.isclose(
        summary.brier_score,
        expected_brier,
    )

    assert math.isclose(
        summary.mean_predicted_probability,
        0.55,
    )

    assert math.isclose(
        summary.empirical_win_rate,
        0.50,
    )

    assert math.isclose(
        summary.coverage,
        1.0,
    )

    assert (
        summary.log_loss > 0
    )


def test_calibration_summary_empty():

    summary = calibration_summary(
        FakeHistory([])
    )

    assert (
        summary.total_predictions
        == 0
    )

    assert (
        summary.evaluated_predictions
        == 0
    )

    assert (
        summary.brier_score
        == 0.0
    )

    assert (
        summary.log_loss
        == 0.0
    )

    assert (
        summary.coverage
        == 0.0
    )


def test_calibration_buckets():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "A",
                        "WIN",
                    ),
                    selection(
                        "B",
                        "LOSS",
                    ),
                ],
            ),
            {
                "A": 0.15,
                "B": 0.85,
            },
        )
    ]

    buckets = calibration_buckets(
        FakeHistory(records),
        bucket_count=10,
    )

    assert len(
        buckets
    ) == 10

    assert (
        buckets[1].predictions
        == 1
    )

    assert (
        buckets[1].wins
        == 1
    )

    assert (
        buckets[8].predictions
        == 1
    )

    assert (
        buckets[8].wins
        == 0
    )


def test_calibration_buckets_invalid_count():

    with pytest.raises(
        TypeError
    ):

        calibration_buckets(
            FakeHistory([]),
            bucket_count=True,
        )

    with pytest.raises(
        ValueError
    ):

        calibration_buckets(
            FakeHistory([]),
            bucket_count=0,
        )


def test_calibration_by_market():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    ),
                    selection(
                        "OVER_2.5",
                        "LOSS",
                    ),
                ],
            ),
            {
                "HOME": 0.70,
                "OVER_2.5": 0.60,
            },
        ),

        add_report(
            make_record(
                2,
                [
                    selection(
                        "HOME",
                        "LOSS",
                    ),
                    selection(
                        "OVER_2.5",
                        "WIN",
                    ),
                ],
            ),
            {
                "HOME": 0.80,
                "OVER_2.5": 0.40,
            },
        ),
    ]

    result = calibration_by_market(
        FakeHistory(records)
    )

    assert set(
        result
    ) == {
        "HOME",
        "OVER_2.5",
    }

    assert (
        result["HOME"]
        .evaluated_predictions
        == 2
    )

    assert (
        result["HOME"]
        .empirical_win_rate
        == 0.5
    )

    assert math.isclose(
        result["HOME"]
        .mean_predicted_probability,
        0.75,
    )

    assert (
        result["OVER_2.5"]
        .evaluated_predictions
        == 2
    )

    assert (
        result["OVER_2.5"]
        .empirical_win_rate
        == 0.5
    )


def test_invalid_probability_is_rejected():

    records = [
        add_report(
            make_record(
                1,
                [
                    selection(
                        "HOME",
                        "WIN",
                    )
                ],
            ),
            {
                "HOME": 1.5
            },
        )
    ]

    with pytest.raises(
        ValueError
    ):

        collect_observations(
            FakeHistory(records)
        )


def test_invalid_history_is_rejected():

    with pytest.raises(
        TypeError
    ):

        calibration_summary(
            None
  )
