from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.dataset_backtest import (
    DATASET_BACKTEST_VERSION,
    DatasetBacktestRunner,
    DatasetBacktestSummary,
    read_dataset_file,
    run_dataset_backtest,
)


def write(
    path: Path,
    content: str,
) -> Path:

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def create_match_files(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:

    stats_1 = write(
        tmp_path / "stats1.csv",
        (
            "home_gf,home_ga,away_gf\n"
            "1.8,1.1,1.4\n"
        ),
    )

    stats_2 = write(
        tmp_path / "stats2.csv",
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.3,1.75,1.05,1.25\n"
        ),
    )

    odds = write(
        tmp_path / "odds.csv",
        (
            "outcome,odds\n"
            "HOME,10.0\n"
            "DRAW,10.0\n"
            "AWAY,10.0\n"
        ),
    )

    return (
        stats_1,
        stats_2,
        odds,
    )


def create_dataset(
    tmp_path: Path,
) -> Path:

    return write(
        tmp_path / "dataset.csv",
        (
            "match_id,statistics_file_1,"
            "statistics_file_2,odds_file,bankroll,"
            "home_goals,away_goals\n"
            "M-001,stats1.csv,stats2.csv,"
            "odds.csv,50000,2,1\n"
        ),
    )


def test_version():

    assert (
        DATASET_BACKTEST_VERSION
        == "Q200-DATASET-BACKTEST-V1"
    )


def test_read_dataset_file(
    tmp_path,
):

    dataset = create_dataset(
        tmp_path
    )

    rows = read_dataset_file(
        dataset
    )

    assert len(
        rows
    ) == 1

    assert (
        rows[0]["match_id"]
        == "M-001"
    )

    assert (
        rows[0]["home_goals"]
        == "2"
    )


def test_dataset_backtest_end_to_end(
    tmp_path,
):

    create_match_files(
        tmp_path
    )

    dataset = create_dataset(
        tmp_path
    )

    history_path = (
        tmp_path
        / "history.db"
    )

    summary = run_dataset_backtest(
        dataset,
        history_path,
    )

    assert isinstance(
        summary,
        DatasetBacktestSummary,
    )

    assert (
        summary.requested_rows
        == 1
    )

    assert (
        summary.processed_rows
        == 1
    )

    assert (
        summary.failed_rows
        == 0
    )

    assert len(
        summary.results
    ) == 1

    assert (
        summary.results[0]
        .settlement_recorded
        is True
    )

    assert (
        summary.evaluation
        .performance
        .total_analysis_records
        == 1
    )

    assert (
        summary.evaluation
        .performance
        .settled_matches
        == 1
    )


def test_runner_uses_relative_paths_from_dataset_directory(
    tmp_path,
):

    create_match_files(
        tmp_path
    )

    dataset = create_dataset(
        tmp_path
    )

    history_path = (
        tmp_path
        / "history.db"
    )

    summary = (
        DatasetBacktestRunner(
            history_path
        ).run_file(
            dataset
        )
    )

    assert (
        summary.processed_rows
        == 1
    )

    assert (
        summary.failed_rows
        == 0
    )


def test_continue_on_error_processes_valid_rows(
    tmp_path,
):

    create_match_files(
        tmp_path
    )

    dataset = write(
        tmp_path / "dataset.csv",
        (
            "match_id,statistics_file_1,"
            "statistics_file_2,odds_file,bankroll,"
            "home_goals,away_goals\n"

            "BAD,missing.csv,stats2.csv,"
            "odds.csv,50000,1,0\n"

            "GOOD,stats1.csv,stats2.csv,"
            "odds.csv,50000,2,1\n"
        ),
    )

    summary = run_dataset_backtest(
        dataset,
        tmp_path / "history.db",
        continue_on_error=True,
    )

    assert (
        summary.requested_rows
        == 2
    )

    assert (
        summary.processed_rows
        == 1
    )

    assert (
        summary.failed_rows
        == 1
    )


def test_failure_is_raised_by_default(
    tmp_path,
):

    dataset = write(
        tmp_path / "dataset.csv",
        (
            "match_id,statistics_file_1,"
            "statistics_file_2,odds_file,bankroll,"
            "home_goals,away_goals\n"

            "BAD,missing1.csv,missing2.csv,"
            "missing3.csv,50000,1,0\n"
        ),
    )

    with pytest.raises(
        FileNotFoundError
    ):

        run_dataset_backtest(
            dataset,
            tmp_path / "history.db",
        )


def test_unknown_dataset_header_is_rejected(
    tmp_path,
):

    dataset = write(
        tmp_path / "dataset.csv",
        (
            "match_id,unknown,"
            "statistics_file_1,statistics_file_2,"
            "odds_file,bankroll,home_goals,away_goals\n"

            "M-001,x,stats1.csv,stats2.csv,"
            "odds.csv,50000,2,1\n"
        ),
    )

    with pytest.raises(
        ValueError
    ):

        read_dataset_file(
            dataset
        )


def test_missing_required_dataset_header_is_rejected(
    tmp_path,
):

    dataset = write(
        tmp_path / "dataset.csv",
        (
            "match_id,statistics_file_1,"
            "statistics_file_2,odds_file,bankroll,"
            "home_goals\n"

            "M-001,stats1.csv,stats2.csv,"
            "odds.csv,50000,2\n"
        ),
    )

    with pytest.raises(
        ValueError
    ):

        read_dataset_file(
            dataset
        )


def test_invalid_bankroll_is_rejected(
    tmp_path,
):

    create_match_files(
        tmp_path
    )

    dataset = write(
        tmp_path / "dataset.csv",
        (
            "match_id,statistics_file_1,"
            "statistics_file_2,odds_file,bankroll,"
            "home_goals,away_goals\n"

            "M-001,stats1.csv,stats2.csv,"
            "odds.csv,0,2,1\n"
        ),
    )

    with pytest.raises(
        ValueError
    ):

        run_dataset_backtest(
            dataset,
            tmp_path / "history.db",
        )
