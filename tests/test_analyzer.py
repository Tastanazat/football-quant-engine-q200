"""
Q200 Engine - File Analyzer Tests

Q200 V3.1
"""

from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.analyzer import run_q200_from_files


def create_csv(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def create_statistics_files(
    tmp_path: Path,
) -> tuple[Path, Path]:

    statistics_1 = (
        tmp_path
        / "statistics_1.csv"
    )

    statistics_2 = (
        tmp_path
        / "statistics_2.csv"
    )

    create_csv(
        statistics_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        statistics_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    return (
        statistics_1,
        statistics_2,
    )


def create_odds_file(
    tmp_path: Path,
) -> Path:

    odds = (
        tmp_path
        / "odds.csv"
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

    return odds


def test_run_q200_from_three_files(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )

    assert (
        result.snapshot.lambda_home
        > 0
    )

    assert (
        result.snapshot.lambda_away
        > 0
    )

    assert set(
        result.no_vig_probabilities
    ) == {
        "HOME",
        "DRAW",
        "AWAY",
    }


def test_three_file_pipeline_produces_ev(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
    )

    assert "HOME" in result.ev
    assert "DRAW" in result.ev
    assert "AWAY" in result.ev

    assert (
        "HOME"
        in result.pessimistic_ev
    )

    assert (
        "DRAW"
        in result.pessimistic_ev
    )

    assert (
        "AWAY"
        in result.pessimistic_ev
    )


def test_odds_file_does_not_unlock_model(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
    )

    assert (
        result.snapshot.locked
        is True
    )


def test_three_file_pipeline_accepts_uncertainty(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
        uncertainty="HIGH",
    )

    assert isinstance(
        result.selections,
        list,
    )


def test_three_file_pipeline_forwards_row_indexes(
    tmp_path,
):

    statistics_1 = (
        tmp_path
        / "statistics_1.csv"
    )

    statistics_2 = (
        tmp_path
        / "statistics_2.csv"
    )

    odds = create_odds_file(
        tmp_path
    )

    create_csv(
        statistics_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.00,2.00,3.00\n"
            "2.00,3.00,4.00\n"
        ),
    )

    create_csv(
        statistics_2,
        (
            "away_ga\n"
            "1.10\n"
            "1.30\n"
        ),
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
        row_index_1=1,
        row_index_2=1,
    )

    assert (
        result.snapshot.locked
        is True
    )


def test_missing_odds_file_is_rejected(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    with pytest.raises(
        FileNotFoundError
    ):

        run_q200_from_files(
            statistics_1,
            statistics_2,
            tmp_path / "missing.csv",
            bankroll=50_000,
        )


def test_invalid_odds_file_is_rejected(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = (
        tmp_path
        / "odds.csv"
    )

    create_csv(
        odds,
        (
            "outcome,odds\n"
            "HOME,1.00\n"
        ),
    )

    with pytest.raises(
        ValueError
    ):

        run_q200_from_files(
            statistics_1,
            statistics_2,
            odds,
            bankroll=50_000,
        )


def test_invalid_bankroll_is_rejected(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    with pytest.raises(
        ValueError
    ):

        run_q200_from_files(
            statistics_1,
            statistics_2,
            odds,
            bankroll=0,
        )


def test_mixed_statistics_and_odds_formats(
    tmp_path,
):

    openpyxl = pytest.importorskip(
        "openpyxl"
    )

    statistics_1 = (
        tmp_path
        / "statistics_1.csv"
    )

    statistics_2 = (
        tmp_path
        / "statistics_2.xlsx"
    )

    odds = (
        tmp_path
        / "odds.xlsx"
    )

    create_csv(
        statistics_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    workbook = (
        openpyxl.Workbook()
    )

    worksheet = (
        workbook.active
    )

    worksheet.append(
        [
            "away_ga",
            "home_xg",
            "home_xga",
            "away_xga",
        ]
    )

    worksheet.append(
        [
            1.30,
            1.75,
            1.05,
            1.25,
        ]
    )

    workbook.save(
        statistics_2
    )

    workbook = (
        openpyxl.Workbook()
    )

    worksheet = (
        workbook.active
    )

    worksheet.append(
        [
            "outcome",
            "odds",
        ]
    )

    worksheet.append(
        [
            "HOME",
            2.10,
        ]
    )

    worksheet.append(
        [
            "DRAW",
            3.40,
        ]
    )

    worksheet.append(
        [
            "AWAY",
            3.80,
        ]
    )

    workbook.save(
        odds
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
    )

    assert (
        result.snapshot.locked
        is True
    )

    assert (
        result.snapshot.lambda_home
        > 0
    )

    assert (
        result.snapshot.lambda_away
        > 0
    )


def test_run_q200_auto_saves_history(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    history_path = (
        tmp_path
        / "history.sqlite"
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
        history_path=history_path,
        match_id="MATCH-001",
    )

    from q200_engine.history import (
        AnalysisHistory,
    )

    history = AnalysisHistory(
        history_path
    )

    assert history.count() == 1

    record = history.get(1)

    assert record is not None
    assert record["match_id"] == "MATCH-001"

    assert (
        record["report"]["model_locked"]
        is True
    )

    assert (
        record["model_version"]
        == "Q200-V3.1"
    )

    assert result.snapshot.locked is True


def test_run_q200_requires_both_history_arguments(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    history_path = (
        tmp_path
        / "history.sqlite"
    )

    with pytest.raises(
        ValueError
    ):

        run_q200_from_files(
            statistics_1,
            statistics_2,
            odds,
            bankroll=50_000,
            history_path=history_path,
        )

    with pytest.raises(
        ValueError
    ):

        run_q200_from_files(
            statistics_1,
            statistics_2,
            odds,
            bankroll=50_000,
            match_id="MATCH-002",
        )


def test_run_q200_history_save_preserves_result(
    tmp_path,
):

    statistics_1, statistics_2 = (
        create_statistics_files(
            tmp_path
        )
    )

    odds = create_odds_file(
        tmp_path
    )

    history_path = (
        tmp_path
        / "history.sqlite"
    )

    result = run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
        history_path=history_path,
        match_id="MATCH-003",
    )

    assert result.snapshot.locked is True
    assert result.snapshot.lambda_home > 0
    assert result.snapshot.lambda_away > 0
