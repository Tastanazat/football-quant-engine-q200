"""
Q200 Engine - Analysis History Tests

Q200 V3.1
"""

from __future__ import annotations

import json

import pytest

from q200_engine.analyzer import (
    run_q200_from_files,
)

from q200_engine.history import (
    HISTORY_SCHEMA_VERSION,
    AnalysisHistory,
)


def create_csv(
    path,
    content,
):
    path.write_text(
        content,
        encoding="utf-8",
    )


def create_result(
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

    return run_q200_from_files(
        stats1,
        stats2,
        odds,
        bankroll=50_000,
    )


def test_history_creates_database(
    tmp_path,
):

    db = (
        tmp_path
        / "history.sqlite"
    )

    history = AnalysisHistory(
        db
    )

    assert db.exists()
    assert history.count() == 0
    assert history.count_completed() == 0


def test_save_and_get_analysis(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "TEAM_A-vs-TEAM_B-2026-09-17",
    )

    assert record_id == 1
    assert history.count() == 1
    assert history.count_completed() == 0

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["id"]
        == 1
    )

    assert (
        record["match_id"]
        == "TEAM_A-vs-TEAM_B-2026-09-17"
    )

    assert (
        record["model_version"]
        == "Q200-V3.1"
    )

    assert (
        record["report_version"]
        == "Q200-REPORT-V1"
    )

    assert (
        record["result_recorded"]
        is False
    )

    assert (
        record["home_goals"]
        is None
    )

    assert (
        record["away_goals"]
        is None
    )

    assert (
        record["report"]
        ["model_locked"]
        is True
    )


def test_history_persists_between_instances(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    db = (
        tmp_path
        / "history.sqlite"
    )

    first = AnalysisHistory(
        db
    )

    record_id = first.save(
        result,
        "MATCH-001",
    )

    second = AnalysisHistory(
        db
    )

    record = second.get(
        record_id
    )

    assert record is not None

    assert (
        record["match_id"]
        == "MATCH-001"
    )

    assert second.count() == 1


def test_list_returns_newest_first(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    history.save(
        result,
        "MATCH-001",
    )

    history.save(
        result,
        "MATCH-002",
    )

    history.save(
        result,
        "MATCH-003",
    )

    records = history.list()

    assert [
        item["match_id"]
        for item in records
    ] == [
        "MATCH-003",
        "MATCH-002",
        "MATCH-001",
    ]


def test_list_limit(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    for index in range(5):

        history.save(
            result,
            f"MATCH-{index}",
        )

    records = history.list(
        limit=2
    )

    assert len(records) == 2


def test_delete_analysis(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-DELETE",
    )

    assert (
        history.delete(
            record_id
        )
        is True
    )

    assert (
        history.get(
            record_id
        )
        is None
    )

    assert history.count() == 0


def test_missing_record_returns_none(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    assert (
        history.get(999)
        is None
    )


def test_invalid_match_id_is_rejected(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    with pytest.raises(
        TypeError
    ):

        history.save(
            result,
            123,
        )

    with pytest.raises(
        ValueError
    ):

        history.save(
            result,
            "   ",
        )


def test_invalid_record_id_is_rejected(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    with pytest.raises(
        TypeError
    ):

        history.get(
            "1"
        )

    with pytest.raises(
        ValueError
    ):

        history.get(
            0
        )

    with pytest.raises(
        TypeError
    ):

        history.delete(
            "1"
        )

    with pytest.raises(
        ValueError
    ):

        history.delete(
            0
        )


def test_invalid_limit_is_rejected(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    with pytest.raises(
        TypeError
    ):

        history.list(
            "10"
        )

    with pytest.raises(
        ValueError
    ):

        history.list(
            0
        )


def test_history_stores_valid_json(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-JSON",
    )

    record = history.get(
        record_id
    )

    assert record is not None

    encoded = json.dumps(
        record["report"],
        ensure_ascii=False,
    )

    decoded = json.loads(
        encoded
    )

    assert (
        decoded["report_version"]
        == "Q200-REPORT-V1"
    )


def test_history_schema_version_is_defined():

    assert (
        HISTORY_SCHEMA_VERSION
        == "Q200-HISTORY-V2"
    )


def test_existing_result_is_not_mutated_by_save(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    before = {
        "fair_odds": dict(
            result.fair_odds
        ),

        "ev": dict(
            result.ev
        ),

        "pessimistic_ev": dict(
            result.pessimistic_ev
        ),

        "selections": [
            dict(item)
            for item in result.selections
        ],
    }

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    history.save(
        result,
        "MATCH-NO-MUTATION",
    )

    assert (
        result.fair_odds
        == before["fair_odds"]
    )

    assert (
        result.ev
        == before["ev"]
    )

    assert (
        result.pessimistic_ev
        == before["pessimistic_ev"]
    )

    assert (
        result.selections
        == before["selections"]
    )


def test_record_match_result(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-RESULT",
    )

    assert (
        history.record_result(
            record_id,
            2,
            1,
        )
        is True
    )

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

    assert (
        record["result_recorded_at"]
        is not None
    )

    assert (
        history.count_completed()
        == 1
    )


def test_record_result_can_be_updated(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-UPDATE",
    )

    history.record_result(
        record_id,
        1,
        0,
    )

    history.record_result(
        record_id,
        3,
        2,
    )

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["home_goals"]
        == 3
    )

    assert (
        record["away_goals"]
        == 2
    )

    assert (
        history.count_completed()
        == 1
    )


def test_record_result_missing_record(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    assert (
        history.record_result(
            999,
            2,
            1,
        )
        is False
    )


def test_record_result_rejects_invalid_record_id(
    tmp_path,
):

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    with pytest.raises(
        TypeError
    ):

        history.record_result(
            "1",
            2,
            1,
        )

    with pytest.raises(
        ValueError
    ):

        history.record_result(
            0,
            2,
            1,
        )


def test_record_result_rejects_invalid_goals(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-INVALID-GOALS",
    )

    with pytest.raises(
        TypeError
    ):

        history.record_result(
            record_id,
            "2",
            1,
        )

    with pytest.raises(
        TypeError
    ):

        history.record_result(
            record_id,
            2,
            "1",
        )

    with pytest.raises(
        ValueError
    ):

        history.record_result(
            record_id,
            -1,
            1,
        )

    with pytest.raises(
        ValueError
    ):

        history.record_result(
            record_id,
            2,
            -1,
        )

    with pytest.raises(
        TypeError
    ):

        history.record_result(
            record_id,
            True,
            1,
        )


def test_list_contains_match_result(
    tmp_path,
):

    result = create_result(
        tmp_path
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "MATCH-LIST-RESULT",
    )

    history.record_result(
        record_id,
        2,
        0,
    )

    records = history.list()

    assert len(records) == 1

    assert (
        records[0]["match_id"]
        == "MATCH-LIST-RESULT"
    )

    assert (
        records[0]["result_recorded"]
        is True
    )

    assert (
        records[0]["home_goals"]
        == 2
    )

    assert (
        records[0]["away_goals"]
        == 0
    )
