"""
Q200 Engine - History Performance Tests

Q200 V3.1
"""

from __future__ import annotations

import math

import pytest

from q200_engine.analyzer import (
    run_q200_from_files,
)

from q200_engine.history import (
    AnalysisHistory,
)

from q200_engine.performance import (
    PERFORMANCE_VERSION,
    PerformanceSummary,
    summarize_history,
)


def create_csv(
    path,
    content,
):

    path.write_text(
        content,
        encoding="utf-8",
    )


def create_history_with_result(
    tmp_path,
    match_id,
    home_goals,
    away_goals,
):

    stats1 = (
        tmp_path
        / f"{match_id}_statistics_1.csv"
    )

    stats2 = (
        tmp_path
        / f"{match_id}_statistics_2.csv"
    )

    odds = (
        tmp_path
        / f"{match_id}_odds.csv"
    )

    create_csv(
        stats1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        stats2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    create_csv(
        odds,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "DRAW,3.40\n"
            "AWAY,3.80\n"
        ),
    )

    result = run_q200_from_files(
        stats1,
        stats2,
        odds,
        bankroll=50_000,
        uncertainty="LOW",
    )

    db = (
        tmp_path
        / "history.sqlite"
    )

    history = AnalysisHistory(
        db
    )

    record_id = history.save(
        result,
        match_id,
    )

    history.record_result(
        record_id,
        home_goals,
        away_goals,
    )

    history.settle_record(
        record_id
    )

    return history, record_id


def test_performance_version():

    assert (
        PERFORMANCE_VERSION
        == "Q200-PERFORMANCE-V1"
    )


def test_empty_history_returns_zero_summary(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    summary = summarize_history(
        history
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
        == 0.0
    )

    assert (
        summary.ending_bankroll
        == 0.0
    )


def test_performance_counts_settled_history(
    tmp_path,
):

    history, _ = (
        create_history_with_result(
            tmp_path,
            "MATCH-001",
            2,
            1,
        )
    )

    summary = summarize_history(
        history,
        starting_bankroll=50_000,
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
        >= 0
    )

    assert (
        summary.starting_bankroll
        == 50_000
    )

    assert math.isclose(
        summary.ending_bankroll,
        (
            50_000
            + summary.total_profit
        ),
    )


def test_unsettled_completed_match_is_not_counted_as_settled(
    tmp_path,
):

    stats1 = (
        tmp_path
        / "statistics_1.csv"
    )

    stats2 = (
        tmp_path
        / "statistics_2.csv"
    )

    odds = (
        tmp_path
        / "odds.csv"
    )

    create_csv(
        stats1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        stats2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    create_csv(
        odds,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "DRAW,3.40\n"
            "AWAY,3.80\n"
        ),
    )

    result = run_q200_from_files(
        stats1,
        stats2,
        odds,
        bankroll=50_000,
        uncertainty="LOW",
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-UNSETTLED",
    )

    history.record_result(
        record_id,
        1,
        1,
    )

    summary = summarize_history(
        history
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


def test_performance_matches_settlement_rows(
    tmp_path,
):

    history, record_id = (
        create_history_with_result(
            tmp_path,
            "MATCH-ROWS",
            2,
            1,
        )
    )

    record = history.get(
        record_id
    )

    assert record is not None

    settlement = record[
        "settlement"
    ]

    assert isinstance(
        settlement,
        dict,
    )

    rows = settlement[
        "selections"
    ]

    expected_stake = sum(
        row["stake"]
        for row in rows
    )

    expected_profit = sum(
        row["profit"]
        for row in rows
    )

    expected_wins = sum(
        1
        for row in rows
        if row["settlement"]
        == "WIN"
    )

    expected_losses = sum(
        1
        for row in rows
        if row["settlement"]
        == "LOSS"
    )

    expected_voids = sum(
        1
        for row in rows
        if row["settlement"]
        == "VOID"
    )

    summary = summarize_history(
        history
    )

    assert (
        summary.total_bets
        == len(rows)
    )

    assert (
        summary.wins
        == expected_wins
    )

    assert (
        summary.losses
        == expected_losses
    )

    assert (
        summary.voids
        == expected_voids
    )

    assert math.isclose(
        summary.total_stake,
        expected_stake,
    )

    assert math.isclose(
        summary.total_profit,
        expected_profit,
    )


def test_performance_multiple_matches(
    tmp_path,
):

    history, first_id = (
        create_history_with_result(
            tmp_path,
            "MATCH-001",
            2,
            1,
        )
    )

    stats1 = (
        tmp_path
        / "second_statistics_1.csv"
    )

    stats2 = (
        tmp_path
        / "second_statistics_2.csv"
    )

    odds = (
        tmp_path
        / "second_odds.csv"
    )

    create_csv(
        stats1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.60,1.20,1.50\n"
        ),
    )

    create_csv(
        stats2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.10,1.60,1.10,1.20\n"
        ),
    )

    create_csv(
        odds,
        (
            "outcome,odds\n"
            "HOME,2.20\n"
            "DRAW,3.30\n"
            "AWAY,3.50\n"
        ),
    )

    result = run_q200_from_files(
        stats1,
        stats2,
        odds,
        bankroll=50_000,
        uncertainty="LOW",
    )

    second_id = history.save(
        result,
        "MATCH-002",
    )

    history.record_result(
        second_id,
        0,
        2,
    )

    history.settle_record(
        second_id
    )

    summary = summarize_history(
        history
    )

    assert (
        summary.total_analysis_records
        == 2
    )

    assert (
        summary.completed_matches
        == 2
    )

    assert (
        summary.settled_matches
        == 2
    )

    assert (
        summary.unsettled_completed_matches
        == 0
    )

    assert (
        summary.total_bets
        >= 0
    )

    assert (
        first_id
        != second_id
    )


def test_starting_bankroll_validation(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

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
