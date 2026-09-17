from __future__ import annotations

import pytest

from q200_engine.data_review import (
    approve_review,
    create_review,
    update_review_field,
)

from q200_engine.ingestion.models import (
    MatchInfo,
)

from q200_engine.statshub_ocr import (
    create_statshub_review,
)

from q200_engine.statshub_review_mapper import (
    STATSHUB_REVIEW_MAPPER_VERSION,
    merge_reviewed_statshub_into_canonical,
    review_to_statshub_data,
)


STATSHUB_TEXT = """
Goals 3.05 1.70 1.35 2 3 1 2 1 1
Corners 9.15 4.30 4.85 4 5 6 8 2 4
Expected Goals (xG) 2.92 1.50 1.41
Shots On Target 10.50 5.65 4.85
Total Shots 26.50 15.05 11.45
Possession 100.00 50.85 49.15
Passes 983.85 498.85 485.00
"""


def make_review():
    return create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
    )


def make_match():
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="LaLiga",
        source="StatsHub",
    )


def test_mapper_version():
    assert (
        STATSHUB_REVIEW_MAPPER_VERSION
        == "Q200-STATSHUB-REVIEW-MAPPER-V1"
    )


def test_unapproved_review_cannot_be_mapped():
    review = make_review()

    assert review.approved is False

    with pytest.raises(
        RuntimeError,
        match="onaylanmalıdır",
    ):
        review_to_statshub_data(
            review,
            match=make_match(),
        )


def test_approved_review_becomes_statshub_data():
    review = make_review()

    approve_review(review)

    data = review_to_statshub_data(
        review,
        match=make_match(),
    )

    assert data.match is not None

    assert (
        data.match.home_team
        == "Real Betis"
    )

    assert (
        data.match.away_team
        == "Getafe"
    )

    assert (
        data.values["goals_avg"]
        == 3.05
    )

    assert (
        data.values["goals_for"]
        == 1.70
    )

    assert (
        data.values["goals_agt"]
        == 1.35
    )

    assert (
        data.values["xg_avg"]
        == 2.92
    )

    assert (
        data.values["shots_on_target_avg"]
        == 10.50
    )

    assert (
        data.values["total_shots_avg"]
        == 26.50
    )

    assert (
        data.values["possession_avg"]
        == 100.00
    )


def test_manual_correction_is_transferred():
    review = make_review()

    update_review_field(
        review,
        "corners_for",
        4.00,
        note="OCR düzeltmesi",
    )

    assert review.approved is False

    approve_review(review)

    data = review_to_statshub_data(
        review,
        match=make_match(),
    )

    assert (
        data.values["corners_for"]
        == 4.00
    )

    assert (
        data.source_metadata[
            "raw_values"
        ]["corners_for"]
        == 4.30
    )

    assert (
        "corners_for"
        in data.source_metadata[
            "changed_fields"
        ]
    )


def test_raw_ocr_text_is_preserved():
    review = make_review()

    approve_review(review)

    data = review_to_statshub_data(
        review,
        match=make_match(),
    )

    assert data.raw_text is not None
    assert "Goals" in data.raw_text
    assert "Corners" in data.raw_text


def test_review_metadata_is_preserved():
    review = make_review()

    review.metadata["test_marker"] = (
        "preserved"
    )

    approve_review(review)

    data = review_to_statshub_data(
        review,
        match=make_match(),
    )

    assert (
        data.source_metadata[
            "review_metadata"
        ]["test_marker"]
        == "preserved"
    )


def test_source_mapper_receives_approved_statshub():
    review = make_review()

    approve_review(review)

    result = (
        merge_reviewed_statshub_into_canonical(
            review,
            match=make_match(),
        )
    )

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )

    assert (
        result.statshub is not None
    )

    assert (
        result.canonical_values[
            "goals_avg"
        ]
        == 3.05
    )

    assert (
        result.canonical_values[
            "possession_avg"
        ]
        == 100.00
    )

    assert (
        result.source_trace[
            "goals_avg"
        ]
        == "StatsHub"
    )


def test_soccerstats_priority_is_preserved():
    review = create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
    )

    approve_review(review)

    from q200_engine.ingestion.models import (
        GoalStats,
        SoccerStatsData,
    )

    soccerstats = SoccerStatsData(
        match=MatchInfo(
            home_team="Real Betis",
            away_team="Getafe",
            source="SoccerSTATS",
        ),
        goals=GoalStats(
            home_gf_per_match=1.0,
        ),
    )

    result = (
        merge_reviewed_statshub_into_canonical(
            review,
            match=make_match(),
            soccerstats=soccerstats,
        )
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.0
    )

    assert (
        result.source_trace[
            "home_gf_per_match"
        ]
        == "SoccerSTATS"
    )

    assert (
        result.canonical_values[
            "goals_avg"
        ]
        == 3.05
    )


def test_wrong_review_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="DataReview",
    ):
        review_to_statshub_data(
            {},
            match=make_match(),
        )
