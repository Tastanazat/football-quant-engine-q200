"""
Q200 Engine - History Performance Tests

Q200 V3.1
"""

from __future__ import annotations

import math

import pytest

from q200_engine.performance import (
    PERFORMANCE_VERSION,
    PerformanceSummary,
    summarize_history,
)


class FakeHistory:
    """
    Performance katmanını History repository'den
    izole eden test double.
    """

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

            if (
                record["id"]
                == record_id
            ):

                return record

        return None


def make_record(
    record_id,
    *,
    completed=True,
    settled=True,
    selections=None,
):

    return {
        "id": record_id,

        "match_id": (
            f"MATCH-{record_id}"
        ),

        "result_recorded": (
            completed
        ),

        "settlement_recorded": (
            settled
        ),

        "settlement": (
            {
                "record_id": record_id,

                "match_id": (
                    f"MATCH-{record_id}"
                ),

                "home_goals": 2,

                "away_goals": 1,

                "selections": (
                    selections or []
                ),
            }
            if settled
            else None
        ),
    }


def row(
    outcome,
    stake,
    profit,
):

    return {
        "outcome": outcome,

        "odds": 2.0,

        "stake": stake,

        "settlement": outcome,

        "profit": profit,

        "home_goals": 2,

        "away_goals": 1,
    }


def test_performance_version():

    assert (
        PERFORMANCE_VERSION
        == "Q200-PERFORMANCE-V1"
    )


def test_empty_history_returns_zero_summary():

    summary = summarize_history(
        FakeHistory([]),
        starting_bankroll=50_000,
    )

    assert isinstance(
        summary,
        PerformanceSummary,
    )

    assert (
        summary.total_analysis_records
        == 0
    )

    assert (
        summary.completed_matches
        == 0
    )

    assert (
        summary.settled_matches
        == 0
    )

    assert (
        summary.unsettled_completed_matches
        == 0
    )

    assert (
        summary.total_bets
        == 0
    )

    assert (
        summary.wins
        == 0
    )

    assert (
        summary.losses
        == 0
    )

    assert (
        summary.voids
        == 0
    )

    assert (
        summary.total_stake
        == 0.0
    )

    assert (
        summary.total_profit
        == 0.0
    )

    assert (
        summary.roi
        == 0.0
    )

    assert (
        summary.hit_rate
        == 0.0
    )

    assert (
        summary.starting_bankroll
        == 50_000
    )

    assert (
        summary.ending_bankroll
        == 50_000
    )

    assert (
        summary.profit
        == 0.0
    )


def test_performance_aggregates_settlement_rows():

    records = [
        make_record(
            1,
            selections=[
                row(
                    "WIN",
                    100.0,
                    100.0,
                ),
                row(
                    "LOSS",
                    50.0,
                    -50.0,
                ),
                row(
                    "VOID",
                    25.0,
                    0.0,
                ),
            ],
        )
    ]

    summary = summarize_history(
        FakeHistory(records),
        starting_bankroll=1_000,
    )

    assert (
        summary.total_analysis_records
        == 1
    )

    assert (
        summary.completed_matches
        == 1
    )

    assert (
        summary.settled_matches
        == 1
    )

    assert (
        summary.unsettled_completed_matches
        == 0
    )

    assert (
        summary.total_bets
        == 3
    )

    assert (
        summary.wins
        == 1
    )

    assert (
        summary.losses
        == 1
    )

    assert (
        summary.voids
        == 1
    )

    assert (
        summary.total_stake
        == 175.0
    )

    assert (
        summary.total_profit
        == 50.0
    )

    assert math.isclose(
        summary.roi,
        50.0 / 175.0,
    )

    assert math.isclose(
        summary.hit_rate,
        0.5,
    )

    assert (
        summary.starting_bankroll
        == 1_000
    )

    assert (
        summary.ending_bankroll
        == 1_050
    )


def test_unsettled_completed_match_is_not_counted_as_settled():

    records = [
        make_record(
            1,
            completed=True,
            settled=False,
        )
    ]

    summary = summarize_history(
        FakeHistory(records)
    )

    assert (
        summary.total_analysis_records
        == 1
    )

    assert (
        summary.completed_matches
        == 1
    )

    assert (
        summary.settled_matches
        == 0
    )

    assert (
        summary.unsettled_completed_matches
        == 1
    )

    assert (
        summary.total_bets
        == 0
    )

    assert (
        summary.total_profit
        == 0.0
    )


def test_uncompleted_match_is_not_counted_as_completed():

    records = [
        make_record(
            1,
            completed=False,
            settled=False,
        )
    ]

    summary = summarize_history(
        FakeHistory(records)
    )

    assert (
        summary.total_analysis_records
        == 1
    )

    assert (
        summary.completed_matches
        == 0
    )

    assert (
        summary.settled_matches
        == 0
    )

    assert (
        summary.unsettled_completed_matches
        == 0
    )


def test_multiple_matches_are_aggregated():

    records = [
        make_record(
            1,
            selections=[
                row(
                    "WIN",
                    100.0,
                    100.0,
                )
            ],
        ),

        make_record(
            2,
            selections=[
                row(
                    "LOSS",
                    100.0,
                    -100.0,
                )
            ],
        ),

        make_record(
            3,
            completed=True,
            settled=False,
        ),
    ]

    summary = summarize_history(
        FakeHistory(records),
        starting_bankroll=5_000,
    )

    assert (
        summary.total_analysis_records
        == 3
    )

    assert (
        summary.completed_matches
        == 3
    )

    assert (
        summary.settled_matches
        == 2
    )

    assert (
        summary.unsettled_completed_matches
        == 1
    )

    assert (
        summary.total_bets
        == 2
    )

    assert (
        summary.wins
        == 1
    )

    assert (
        summary.losses
        == 1
    )

    assert (
        summary.voids
        == 0
    )

    assert (
        summary.total_stake
        == 200.0
    )

    assert (
        summary.total_profit
        == 0.0
    )

    assert (
        summary.roi
        == 0.0
    )

    assert (
        summary.hit_rate
        == 0.5
    )

    assert (
        summary.ending_bankroll
        == 5_000
    )


def test_invalid_settlement_is_rejected():

    records = [
        make_record(
            1,
            selections=[
                row(
                    "UNKNOWN",
                    100.0,
                    0.0,
                )
            ],
        )
    ]

    with pytest.raises(
        ValueError
    ):

        summarize_history(
            FakeHistory(records)
        )


def test_invalid_bankroll_is_rejected():

    history = FakeHistory([])

    with pytest.raises(
        ValueError
    ):

        summarize_history(
            history,
            starting_bankroll=-1,
        )

    with pytest.raises(
        ValueError
    ):

        summarize_history(
            history,
            starting_bankroll="abc",
        )

    with pytest.raises(
        TypeError
    ):

        summarize_history(
            history,
            starting_bankroll=True,
        )


def test_invalid_history_is_rejected():

    with pytest.raises(
        TypeError
    ):

        summarize_history(
            None
        )
