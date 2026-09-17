from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from q200_engine.data_review import (
    approve_review,
    update_review_field,
)

from q200_engine.statshub_ocr import (
    STATSHUB_OCR_VERSION,
    canonical_stat_name,
    create_statshub_review,
    extract_numbers,
    flatten_statshub_summary,
    parse_statshub_table_text,
    parse_statshub_text,
)


STATSHUB_TEXT = """
Goals 3.05 1.70 1.35 2 3 1 2 1 1 2 1 2
Corners 9.15 4.30 4.85 4 5 6 8 2 4 4 4 8
Cards 4.20 1.95 2.25 0 3 3 1 1 3 1 0 3
Crosses 6.30 3.30 3.00 3 3 1 7 3 4 3 1 5
Big Chance Created 4.60 2.35 2.25 7 3 1 2 2 1 4 1 2
Big Chance Missed 2.55 1.20 1.35 5 1 0 1 1 1 2 1 2
Big Chance Scored 2.20 1.20 1.00 2 2 1 1 1 0 2 1 0
Expected Goals (xG) 2.92 1.50 1.41 3.75 1.80 0.93 1.92 0.71 1.24 1.51 0.97 1.80
Shots On Target 10.50 5.65 4.85 12 5 5 6 3 7 8 2 7
Shots In The Box 16.05 8.40 7.65 20 10 4 6 9 6 3 11 4
Total Shots 26.50 15.05 11.45 26 20 10 20 15 18 18 7 16
Shots Outside The Box 10.45 6.65 3.80 6 10 6 4 9 9 12 4 5
Clearances 43.15 24.15 19.00 29 24 21 32 34 25 22 23 31
Dispossessed 16.15 7.75 8.40 8 9 1 9 8 6 4 7 11
Errors Lead To Goal 0.40 0.25 0.15 0 0 0 1 0 0 0 1 0
Errors Lead To Shot 1.60 0.40 1.10 0 1 1 1 0 1 0 0 1
Fouls 21.65 10.50 11.05 8 13 11 7 9 11 9 11 8
Goalkeeper Saves 7.25 3.40 3.85 7 0 6 4 3 3 6 6 1
Interception Won 17.20 9.30 7.90 7 4 8 7 10 7 3 8 10
Tackles 31.25 17.80 13.45 22 9 26 18 20 6 3 8 22
Free Kicks 25.90 13.95 11.95 12 15 25 10 11 15 8 9 5
Goal Kicks 12.95 5.55 7.40 8 3 7 7 9 5 8 9 6
Throw Ins 31.35 15.45 15.90 19 20 11 10 19 11 14 15 15
Possession 100.00 50.85 49.15 38 55 42 60 58 48 64 37 45
Offsides 4.70 1.70 3.00 2 0 1 2 1 1 1 4 3
Passes 983.85 498.85 485.00 378 564 412 573 540 481 618 411 442
Touches In Opp Box 45.70 23.95 21.75 37 31 18 46 18 29 10 18 38
Red Cards 0.15 0.05 0.10 0 0 0 0 0 0 0 0 0
Yellow Cards 4.05 1.90 2.15 0 3 3 1 1 3 1 0 3
"""


def test_statshub_real_labels_are_mapped() -> None:
    assert canonical_stat_name("Goals") == "goals"
    assert canonical_stat_name("Comers") == "corners"
    assert canonical_stat_name("Corners") == "corners"
    assert canonical_stat_name("Expected Goals (xG)") == "xg"
    assert canonical_stat_name("Shots On Target") == "shots_on_target"
    assert canonical_stat_name("Shots In The Box") == "shots_in_box"
    assert canonical_stat_name("Total Shots") == "total_shots"
    assert canonical_stat_name("Possession") == "possession"
    assert canonical_stat_name("Touches In Opp Box") == "touches_in_opp_box"


def test_extract_numbers_supports_decimals_and_percent() -> None:
    assert extract_numbers(
        "Possession 50.85 49.15"
    ) == [50.85, 49.15]

    assert extract_numbers(
        "xG 2,92 1,50"
    ) == [2.92, 1.50]

    assert extract_numbers(
        "Possession 50.85%"
    ) == [50.85]


def test_parse_statshub_keeps_avg_for_agt_separate() -> None:
    result = parse_statshub_table_text(
        STATSHUB_TEXT
    )

    assert result["goals"] == {
        "avg": 3.05,
        "for": 1.70,
        "agt": 1.35,
    }

    assert result["shots_on_target"] == {
        "avg": 10.50,
        "for": 5.65,
        "agt": 4.85,
    }

    assert result["possession"] == {
        "avg": 100.00,
        "for": 50.85,
        "agt": 49.15,
    }


def test_parse_statshub_ignores_match_history_columns() -> None:
    result = parse_statshub_text(
        "Goals 3.05 1.70 1.35 2 3 1 2 1 1 2 1 2"
    )

    assert result["goals"] == 3.05


def test_flatten_summary_creates_unambiguous_field_names() -> None:
    table = parse_statshub_table_text(
        STATSHUB_TEXT
    )

    values = flatten_statshub_summary(
        table
    )

    assert values["goals_avg"] == 3.05
    assert values["goals_for"] == 1.70
    assert values["goals_agt"] == 1.35

    assert values["corners_avg"] == 9.15
    assert values["corners_for"] == 4.30
    assert values["corners_agt"] == 4.85

    assert values["possession_for"] == 50.85


def test_parse_single_column() -> None:
    result = parse_statshub_text(
        STATSHUB_TEXT,
        value_column="for",
    )

    assert result["goals"] == 1.70
    assert result["corners"] == 4.30
    assert result["shots_on_target"] == 5.65


def test_create_review_starts_unapproved() -> None:
    review = create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
    )

    assert review.approved is False
    assert review.source_type == "OCR"

    assert (
        review.metadata["ocr_version"]
        == STATSHUB_OCR_VERSION
    )

    assert review.metadata["columns"] == [
        "avg",
        "for",
        "agt",
    ]

    assert (
        review.fields["corners_for"].value
        == 4.30
    )

    assert (
        review.fields["possession_for"].value
        == 50.85
    )


def test_manual_correction_preserves_ocr_value() -> None:
    review = create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
    )

    update_review_field(
        review,
        "corners_for",
        4.00,
        note="OCR sonrası manuel düzeltme.",
    )

    assert review.approved is False

    assert (
        review.fields[
            "corners_for"
        ].raw_value
        == 4.30
    )

    assert (
        review.fields[
            "corners_for"
        ].value
        == 4.00
    )

    assert (
        review.fields[
            "corners_for"
        ].status
        == "MANUAL"
    )

    approve_review(review)

    assert (
        review.values()["corners_for"]
        == 4.00
    )


def test_create_review_can_use_injected_ocr_engine(
    tmp_path: Path,
) -> None:
    from PIL import Image

    image_path = (
        tmp_path / "stats.jpg"
    )

    image = Image.new(
        "RGB",
        (20, 20),
        "white",
    )

    image.save(
        image_path
    )

    image.close()

    def fake_ocr(
        _image: Any,
    ) -> str:
        return (
            "Goals 3.05 1.70 1.35\n"
            "Corners 9.15 4.30 4.85"
        )

    review = create_statshub_review(
        image_path,
        ocr_engine=fake_ocr,
    )

    assert (
        review.fields[
            "goals_avg"
        ].value
        == 3.05
    )

    assert (
        review.fields[
            "corners_agt"
        ].value
        == 4.85
    )


def test_invalid_column_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="value_column",
    ):
        parse_statshub_text(
            STATSHUB_TEXT,
            value_column="wrong",
        )
