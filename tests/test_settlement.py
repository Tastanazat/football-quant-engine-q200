"""
Q200 Engine - Analysis Settlement Tests

Q200 V3.1
"""

from __future__ import annotations

import pytest

from q200_engine.analyzer import (
    run_q200_from_files,
)

from q200_engine.history import (
    AnalysisHistory,
)

from q200_engine.settlement import (
    SETTLEMENT_VERSION,
    settle_analysis_record,
)


def create_csv(
    path,
    content,
):

    path.write_text(
        content,
        encoding="utf-8",
    )


def create_record(
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
        "MATCH-SETTLE",
    )

    return history.get(
        record_id
    )


def test_settlement_version():

    assert (
        SETTLEMENT_VERSION
        == "Q200-SETTLEMENT-V1"
    )


def test_settle_analysis_record_returns_match_result(
    tmp_path,
):

    record = create_record(
        tmp_path
    )

    settlement = settle_analysis_record(
        record,
        home_goals=2,
        away_goals=1,
    )

    assert (
        settlement["record_id"]
        == record["id"]
    )

    assert (
        settlement["match_id"]
        == "MATCH-SETTLE"
    )

    assert (
        settlement["home_goals"]
        == 2
    )

    assert (
        settlement["away_goals"]
        == 1
    )

    assert isinstance(
        settlement["selections"],
        list,
    )

    assert "summary" in settlement


def test_settlement_only_processes_eligible_selections(
    tmp_path,
):

    record = create_record(
        tmp_path
    )

    settlement = settle_analysis_record(
        record,
        home_goals=2,
        away_goals=1,
    )

    assert all(
        item["settlement"]
        in {
            "WIN",
            "LOSS",
            "VOID",
        }
        for item
        in settlement["selections"]
    )

    assert all(
        item["stake"] >= 0
        for item
        in settlement["selections"]
    )


def test_settlement_summary_matches_rows(
    tmp_path,
):

    record = create_record(
        tmp_path
    )

    settlement = settle_analysis_record(
        record,
        home_goals=2,
        away_goals=1,
    )

    rows = settlement[
        "selections"
    ]

    summary = settlement[
        "summary"
    ]

    assert (
        summary["total_bets"]
        == len(rows)
    )

    assert (
        summary["wins"]
        == sum(
            1
            for row in rows
            if row["settlement"]
            == "WIN"
        )
    )

    assert (
        summary["losses"]
        == sum(
            1
            for row in rows
            if row["settlement"]
            == "LOSS"
        )
    )

    assert (
        summary["voids"]
        == sum(
            1
            for row in rows
            if row["settlement"]
            == "VOID"
        )
    )

    assert (
        summary["total_stake"]
        == sum(
            row["stake"]
            for row in rows
        )
    )

    assert (
        summary["total_profit"]
        == sum(
            row["profit"]
            for row in rows
        )
    )


def test_home_selection_wins_when_home_wins():

    record = {
        "id": 1,
        "match_id": "MATCH-1",
        "report": {
            "selection": {
                "selections": [
                    {
                        "outcome": "HOME",
                        "odds": 2.0,
                        "stake": 100.0,
                        "eligible": True,
                    },
                    {
                        "outcome": "AWAY",
                        "odds": 2.0,
                        "stake": 100.0,
                        "eligible": False,
                    },
                ]
            }
        },
    }

    settlement = settle_analysis_record(
        record,
        2,
        1,
    )

    assert (
        len(
            settlement["selections"]
        )
        == 1
    )

    assert (
        settlement[
            "selections"
        ][0]["settlement"]
        == "WIN"
    )

    assert (
        settlement[
            "selections"
        ][0]["profit"]
        == 100.0
    )


def test_draw_selection_wins_on_draw():

    record = {
        "id": 2,
        "match_id": "MATCH-2",
        "report": {
            "selection": {
                "selections": [
                    {
                        "outcome": "DRAW",
                        "odds": 3.0,
                        "stake": 100.0,
                        "eligible": True,
                    }
                ]
            }
        },
    }

    settlement = settle_analysis_record(
        record,
        1,
        1,
    )

    assert (
        settlement[
            "selections"
        ][0]["settlement"]
        == "WIN"
    )

    assert (
        settlement[
            "selections"
        ][0]["profit"]
        == 200.0
    )


def test_away_selection_loses_when_home_wins():

    record = {
        "id": 3,
        "match_id": "MATCH-3",
        "report": {
            "selection": {
                "selections": [
                    {
                        "outcome": "AWAY",
                        "odds": 2.0,
                        "stake": 100.0,
                        "eligible": True,
                    }
                ]
            }
        },
    }

    settlement = settle_analysis_record(
        record,
        2,
        0,
    )

    assert (
        settlement[
            "selections"
        ][0]["settlement"]
        == "LOSS"
    )

    assert (
        settlement[
            "selections"
        ][0]["profit"]
        == -100.0
    )


def test_no_eligible_selection_returns_zero_summary():

    record = {
        "id": 4,
        "match_id": "MATCH-4",
        "report": {
            "selection": {
                "selections": [
                    {
                        "outcome": "HOME",
                        "odds": 2.0,
                        "stake": 0.0,
                        "eligible": False,
                    }
                ]
            }
        },
    }

    settlement = settle_analysis_record(
        record,
        2,
        1,
    )

    assert (
        settlement["selections"]
        == []
    )

    assert (
        settlement["summary"]
        ["total_bets"]
        == 0
    )

    assert (
        settlement["summary"]
        ["total_profit"]
        == 0.0
    )

    assert (
        settlement["summary"]
        ["roi"]
        == 0.0
    )


def test_invalid_goals_are_rejected(
    tmp_path,
):

    record = create_record(
        tmp_path
    )

    with pytest.raises(
        TypeError
    ):

        settle_analysis_record(
            record,
            "2",
            1,
        )

    with pytest.raises(
        TypeError
    ):

        settle_analysis_record(
            record,
            2,
            "1",
        )

    with pytest.raises(
        ValueError
    ):

        settle_analysis_record(
            record,
            -1,
            1,
        )


def test_invalid_record_is_rejected():

    with pytest.raises(
        TypeError
    ):

        settle_analysis_record(
            None,
            2,
            1,
        )

    with pytest.raises(
        ValueError
    ):

        settle_analysis_record(
            {},
            2,
            1,
        )
