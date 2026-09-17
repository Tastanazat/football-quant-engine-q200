from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.data_review import (
    approve_review,
    update_review_field,
)
from q200_engine.statistics_loader import (
    load_team_stats_from_reviews,
)
from q200_engine.statistics_reader import (
    read_statistics_review,
)


def create_csv(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_read_statistics_review_creates_unapproved_review(
    tmp_path,
):
    file_path = (
        tmp_path
        / "stats.csv"
    )

    create_csv(
        file_path,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    review = read_statistics_review(
        file_path
    )

    assert review.approved is False

    assert review.source_type == "CSV"

    assert (
        review.fields["home_gf"].value
        == "1.80"
    )

    assert (
        review.fields["home_gf"].raw_value
        == "1.80"
    )

    assert (
        review.fields["home_gf"].status
        == "AUTO"
    )


def test_unapproved_review_cannot_build_team_stats(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    with pytest.raises(
        RuntimeError,
        match="onaylanmadan",
    ):
        load_team_stats_from_reviews(
            review_1,
            review_2,
        )


def test_corrected_values_reach_team_stats_after_approval(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    update_review_field(
        review_1,
        "home_gf",
        2.00,
    )

    approve_review(
        review_1
    )

    approve_review(
        review_2
    )

    stats = load_team_stats_from_reviews(
        review_1,
        review_2,
    )

    assert stats.home_gf == 2.00
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40

    assert (
        review_1.fields[
            "home_gf"
        ].raw_value
        == "1.80"
    )

    assert (
        review_1.fields[
            "home_gf"
        ].value
        == 2.00
    )

    assert (
        review_1.fields[
            "home_gf"
        ].status
        == "MANUAL"
    )


def test_review_one_has_priority_after_manual_correction(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "home_gf,away_ga\n"
            "3.50,1.30\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    update_review_field(
        review_1,
        "home_gf",
        2.20,
    )

    approve_review(
        review_1
    )

    approve_review(
        review_2
    )

    stats = load_team_stats_from_reviews(
        review_1,
        review_2,
    )

    assert stats.home_gf == 2.20
    assert stats.away_ga == 1.30


def test_manual_change_after_approval_blocks_model(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "away_ga\n"
            "1.30\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    approve_review(
        review_1
    )

    approve_review(
        review_2
    )

    update_review_field(
        review_1,
        "away_gf",
        1.60,
    )

    with pytest.raises(
        RuntimeError,
        match="onaylanmadan",
    ):
        load_team_stats_from_reviews(
            review_1,
            review_2,
        )


def test_pipeline_from_reviews_requires_approval(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    from q200_engine.file_pipeline import (
        run_pipeline_from_reviews,
    )

    with pytest.raises(
        RuntimeError,
        match="onaylanmadan",
    ):
        run_pipeline_from_reviews(
            review_1,
            review_2,
            {
                "HOME": 2.0,
                "DRAW": 3.5,
                "AWAY": 4.0,
            },
            bankroll=50_000,
        )


def test_pipeline_from_approved_reviews_uses_corrected_value(
    tmp_path,
):
    file_1 = (
        tmp_path
        / "stats1.csv"
    )

    file_2 = (
        tmp_path
        / "stats2.csv"
    )

    create_csv(
        file_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        file_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    review_1 = read_statistics_review(
        file_1
    )

    review_2 = read_statistics_review(
        file_2
    )

    update_review_field(
        review_1,
        "home_gf",
        2.50,
    )

    approve_review(
        review_1
    )

    approve_review(
        review_2
    )

    from q200_engine.file_pipeline import (
        run_pipeline_from_reviews,
    )

    result = run_pipeline_from_reviews(
        review_1,
        review_2,
        {
            "HOME": 2.0,
            "DRAW": 3.5,
            "AWAY": 4.0,
        },
        bankroll=50_000,
    )

    assert (
        result.snapshot.locked
        is True
    )

    expected_lambda = (
        0.35 * 2.50
        + 0.35 * 1.30
        + 0.15 * 1.75
        + 0.15 * 1.25
    )

    assert (
        result.snapshot.lambda_home
        == pytest.approx(
            expected_lambda
        )
    )
