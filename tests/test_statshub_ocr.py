from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.data_review import (
    approve_review,
    update_review_field,
)

from q200_engine.statshub_ocr import (
    STATSHUB_OCR_VERSION,
    StatsHubOCRError,
    canonical_stat_name,
    create_statshub_review,
    extract_numbers,
    parse_statshub_table_text,
    parse_statshub_text,
)


STATSHUB_TEXT = """
Goals 3.05 1.70 1.35
Corners 9.15 4.30 4.85
Cards 4.20 1.95 2.25
Big Chance Created 4.60 2.35 2.25
Big Chance Missed 2.55 1.20 1.35
Expected Goals (xG) 2.92 1.50 1.41
Shots On Target 10.50 5.65 4.85
Shots In The Box 16.05 8.40 7.65
Total Shots 26.50 15.05 11.45
Shots Outside The Box 10.45 6.65 3.80
Possession 100.00 50.85 49.15
Passes 983.85 498.85 485.00
Touches In Opp Box 45.70 23.95 21.75
Red Cards 0.15 0.05 0.10
Yellow Cards 4.05 1.90 2.15
"""


def test_real_statshub_labels_are_mapped() -> None:

    assert (
        canonical_stat_name("Goals")
        == "goals"
    )

    assert (
        canonical_stat_name(
            "Expected Goals (xG)"
        )
        == "xg"
    )

    assert (
        canonical_stat_name(
            "Shots On Target"
        )
        == "shots_on_target"
    )

    assert (
        canonical_stat_name(
            "Possession"
        )
        == "possession"
    )

    assert (
        canonical_stat_name(
            "Corners"
        )
        == "corners"
    )

    assert (
        canonical_stat_name(
            "Touches In Opp Box"
        )
        == "touches_in_opp_box"
    )


def test_extract_numbers_supports_decimal_and_percent() -> None:

    assert extract_numbers(
        "Possession 50.85 49.15"
    ) == [
        50.85,
        49.15,
    ]

    assert extract_numbers(
        "Possession 50.85%"
    ) == [
        50.85,
    ]


def test_parse_statshub_avg_values() -> None:

    result = parse_statshub_text(
        STATSHUB_TEXT
    )

    assert result["goals"] == 3.05
    assert result["corners"] == 9.15
    assert result["xg"] == 2.92
    assert result["shots_on_target"] == 10.50
    assert result["shots_in_box"] == 16.05
    assert result["total_shots"] == 26.50
    assert result["shots_outside_box"] == 10.45
    assert result["possession"] == 100.00
    assert result["passes"] == 983.85


def test_parse_statshub_for_values() -> None:

    result = parse_statshub_text(
        STATSHUB_TEXT,
        value_column="for",
    )

    assert result["goals"] == 1.70
    assert result["corners"] == 4.30
    assert result["shots_on_target"] == 5.65
    assert result["possession"] == 50.85


def test_parse_statshub_agt_values() -> None:

    result = parse_statshub_text(
        STATSHUB_TEXT,
        value_column="agt",
    )

    assert result["goals"] == 1.35
    assert result["corners"] == 4.85
    assert result["shots_on_target"] == 4.85
    assert result["possession"] == 49.15


def test_parse_statshub_table_preserves_all_three_columns() -> None:

    result = parse_statshub_table_text(
        STATSHUB_TEXT
    )

    assert result["goals"] == {
        "avg": 3.05,
        "for": 1.70,
        "agt": 1.35,
    }

    assert result["corners"] == {
        "avg": 9.15,
        "for": 4.30,
        "agt": 4.85,
    }


def test_create_statshub_review_starts_unapproved() -> None:

    review = create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
        confidence={
            "shots_on_target": 0.91,
            "possession": 0.72,
        },
    )

    assert review.approved is False

    assert review.source_type == "OCR"

    assert review.version != ""

    assert (
        review.metadata["ocr_version"]
        == STATSHUB_OCR_VERSION
    )

    assert (
        review.fields[
            "shots_on_target"
        ].value
        == 10.50
    )

    assert (
        review.fields[
            "possession"
        ].value
        == 100.00
    )

    assert (
        "possession"
        in review.low_confidence_fields
    )


def test_statshub_review_manual_correction_keeps_raw_value() -> None:

    review = create_statshub_review(
        "statshub.jpg",
        ocr_text=STATSHUB_TEXT,
    )

    update_review_field(
        review,
        "corners",
        8.0,
        note="OCR kontrolü sonrası düzeltildi.",
    )

    assert review.approved is False

    assert (
        review.fields[
            "corners"
        ].raw_value
        == 9.15
    )

    assert (
        review.fields[
            "corners"
        ].value
        == 8.0
    )

    assert (
        review.fields[
            "corners"
        ].status
        == "MANUAL"
    )

    approve_review(
        review
    )

    assert (
        review.values()["corners"]
        == 8.0
    )


def test_statshub_review_requires_recognized_data() -> None:

    with pytest.raises(
        StatsHubOCRError,
        match="tanınan statistics alanı",
    ):

        create_statshub_review(
            "empty.jpg",
            ocr_text="hello world",
        )


def test_statshub_review_can_use_injected_ocr_engine(
    tmp_path: Path,
) -> None:

    image_path = (
        tmp_path
        / "stats.jpg"
    )

    from PIL import Image

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
        _image,
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
            "goals"
        ].value
        == 3.05
    )

    assert (
        review.fields[
            "corners"
        ].value
        == 9.15
    )
