from __future__ import annotations

import pytest

from q200_engine.backtest_runner import (
    BACKTEST_RUNNER_VERSION,
    BacktestRunItem,
    BacktestRunSummary,
    BacktestRunner,
    run_history_backtest,
)


class FakeHistory:

    def __init__(self):

        self.records = {
            1: {"id": 1},
            2: {"id": 2},
        }

        self.calls = []

    def get(
        self,
        record_id,
    ):

        return self.records.get(
            record_id
        )

    def record_result(
        self,
        record_id,
        home_goals,
        away_goals,
    ):

        self.calls.append(
            (
                "record_result",
                record_id,
                home_goals,
                away_goals,
            )
        )

        return True

    def settle_record(
        self,
        record_id,
    ):

        self.calls.append(
            (
                "settle_record",
                record_id,
            )
        )

        if record_id == 1:

            return {
                "summary": {
                    "total_bets": 2,
                    "wins": 1,
                    "losses": 1,
                    "voids": 0,
                    "total_stake": 150.0,
                    "total_profit": 50.0,
                }
            }

        return {
            "summary": {
                "total_bets": 1,
                "wins": 1,
                "losses": 0,
                "voids": 0,
                "total_stake": 100.0,
                "total_profit": 100.0,
            }
        }


def test_version():

    assert (
        BACKTEST_RUNNER_VERSION
        == "Q200-BACKTEST-RUNNER-V1"
    )


def test_run_one_processes_result_then_settlement():

    history = FakeHistory()

    runner = BacktestRunner(
        history
    )

    result = runner.run_one(
        1,
        2,
        1,
    )

    assert isinstance(
        result,
        BacktestRunItem,
    )

    assert result.record_id == 1
    assert result.home_goals == 2
    assert result.away_goals == 1
    assert result.total_bets == 2
    assert result.wins == 1
    assert result.losses == 1
    assert result.total_stake == 150.0
    assert result.total_profit == 50.0

    assert history.calls == [
        (
            "record_result",
            1,
            2,
            1,
        ),
        (
            "settle_record",
            1,
        ),
    ]


def test_run_aggregates_multiple_results():

    history = FakeHistory()

    summary = run_history_backtest(
        history,
        [
            {
                "record_id": 1,
                "home_goals": 2,
                "away_goals": 1,
            },
            {
                "record_id": 2,
                "home_goals": 0,
                "away_goals": 1,
            },
        ],
    )

    assert isinstance(
        summary,
        BacktestRunSummary,
    )

    assert summary.requested_records == 2
    assert summary.processed_records == 2
    assert summary.failed_records == 0
    assert summary.total_bets == 3
    assert summary.wins == 2
    assert summary.losses == 1
    assert summary.total_stake == 250.0
    assert summary.total_profit == 150.0
    assert len(
        summary.results
    ) == 2


def test_missing_record_fails():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        ValueError
    ):

        runner.run_one(
            999,
            1,
            0,
        )


def test_invalid_record_id_is_rejected():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        TypeError
    ):

        runner.run_one(
            True,
            1,
            0,
        )

    with pytest.raises(
        ValueError
    ):

        runner.run_one(
            0,
            1,
            0,
        )


def test_invalid_goals_are_rejected():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        TypeError
    ):

        runner.run_one(
            1,
            True,
            0,
        )

    with pytest.raises(
        ValueError
    ):

        runner.run_one(
            1,
            -1,
            0,
        )

    with pytest.raises(
        TypeError
    ):

        runner.run_one(
            1,
            1,
            True,
        )

    with pytest.raises(
        ValueError
    ):

        runner.run_one(
            1,
            1,
            -1,
        )


def test_missing_item_fields_are_rejected():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        ValueError
    ):

        runner.run(
            [
                {
                    "record_id": 1,
                    "home_goals": 1,
                }
            ]
        )


def test_non_dict_item_is_rejected():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        TypeError
    ):

        runner.run(
            [1]
        )


def test_continue_on_error_keeps_valid_records():

    history = FakeHistory()

    runner = BacktestRunner(
        history
    )

    summary = runner.run(
        [
            {
                "record_id": 999,
                "home_goals": 1,
                "away_goals": 0,
            },
            {
                "record_id": 1,
                "home_goals": 2,
                "away_goals": 1,
            },
        ],
        continue_on_error=True,
    )

    assert summary.requested_records == 2
    assert summary.processed_records == 1
    assert summary.failed_records == 1
    assert summary.total_bets == 2


def test_continue_on_error_validation():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        TypeError
    ):

        runner.run(
            [],
            continue_on_error=1,
        )


def test_results_must_be_iterable_of_records():

    runner = BacktestRunner(
        FakeHistory()
    )

    with pytest.raises(
        TypeError
    ):

        runner.run(
            {"record_id": 1}
        )

    with pytest.raises(
        TypeError
    ):

        runner.run(
            "bad"
        )
