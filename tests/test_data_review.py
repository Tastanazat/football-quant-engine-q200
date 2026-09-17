from __future__ import annotations

import pytest

from q200_engine.data_review import (
    DATA_REVIEW_VERSION,
    DataReview,
    ReviewField,
    approve_review,
    create_review,
    review_to_dict,
    reviewed_values,
    revoke_review,
    update_review_field,
)


def test_create_review_preserves_raw_values_and_is_not_approved() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="OCR",
        source_file="statshub.jpg",
        values={
            "shots": "14",
            "possession": "47%",
            "corners": "3",
        },
        confidence={
            "shots": 0.91,
            "possession": 0.72,
        },
    )

    assert review.version == DATA_REVIEW_VERSION
    assert review.approved is False

    assert review.raw_values() == {
        "shots": "14",
        "possession": "47%",
        "corners": "3",
    }

    assert review.fields["shots"].status == "AUTO"
    assert review.fields["possession"].confidence == 0.72

    assert "possession" in review.low_confidence_fields


def test_manual_edit_preserves_original_value() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="OCR",
        source_file="statshub.jpg",
        values={
            "corners": "3",
        },
    )

    update_review_field(
        review,
        "corners",
        4,
        note="OCR yanlış okudu.",
    )

    assert review.approved is False

    assert review.fields["corners"].raw_value == "3"
    assert review.fields["corners"].value == 4
    assert review.fields["corners"].status == "MANUAL"

    assert review.manual_field_count == 1
    assert review.changed_fields == ["corners"]


def test_manual_edit_invalidates_existing_approval() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="OCR",
        source_file="statshub.jpg",
        values={
            "shots": "14",
        },
    )

    approve_review(review)

    assert review.approved is True
    assert review.review_status() == "APPROVED"

    update_review_field(
        review,
        "shots",
        15,
    )

    assert review.approved is False
    assert review.review_status() == "MANUAL_REVIEW_REQUIRED"


def test_unapproved_review_cannot_enter_model() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="PDF",
        source_file="soccerstats.pdf",
        values={
            "home_gf": 2.0,
        },
    )

    with pytest.raises(
        RuntimeError,
        match="onaylanmadan",
    ):
        reviewed_values(review)


def test_approved_review_returns_corrected_values() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="OCR",
        source_file="statshub.jpg",
        values={
            "shots": "14",
            "possession": "47%",
        },
    )

    update_review_field(
        review,
        "shots",
        15,
    )

    approve_review(review)

    assert reviewed_values(review) == {
        "shots": 15,
        "possession": "47%",
    }

    assert review.raw_values()["shots"] == "14"


def test_revoke_review_blocks_model_again() -> None:
    review = create_review(
        review_id="match-1-stats",
        source_type="OCR",
        source_file="statshub.jpg",
        values={
            "corners": 4,
        },
    )

    approve_review(review)

    assert reviewed_values(review) == {
        "corners": 4,
    }

    revoke_review(review)

    assert review.approved is False

    with pytest.raises(
        RuntimeError,
        match="onaylanmadan",
    ):
        reviewed_values(review)


def test_empty_review_cannot_be_approved() -> None:
    review = DataReview(
        review_id="empty",
        source_type="MANUAL",
        source_file="manual",
    )

    with pytest.raises(
        ValueError,
        match="Boş review",
    ):
        review.approve()


def test_review_field_rejects_invalid_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="0-1",
    ):
        ReviewField(
            field="shots",
            raw_value=10,
            value=10,
            source="OCR",
            confidence=1.5,
        )


def test_review_field_rejects_invalid_source() -> None:
    with pytest.raises(
        ValueError,
        match="Geçersiz review source",
    ):
        ReviewField(
            field="shots",
            raw_value=10,
            value=10,
            source="UNKNOWN",
        )


def test_review_field_rejects_invalid_status() -> None:
    with pytest.raises(
        ValueError,
        match="Geçersiz review status",
    ):
        ReviewField(
            field="shots",
            raw_value=10,
            value=10,
            source="OCR",
            status="UNKNOWN",
        )


def test_review_serialization_contains_raw_and_corrected_values() -> None:
    review = create_review(
        review_id="match-1",
        source_type="OCR",
        source_file="stats.jpg",
        values={
            "shots": 14,
            "corners": 3,
        },
    )

    update_review_field(
        review,
        "corners",
        4,
        note="Manuel düzeltme",
    )

    data = review_to_dict(review)

    assert data["review_id"] == "match-1"

    assert data["fields"]["shots"]["raw_value"] == 14
    assert data["fields"]["shots"]["value"] == 14
    assert data["fields"]["shots"]["status"] == "AUTO"

    assert data["fields"]["corners"]["raw_value"] == 3
    assert data["fields"]["corners"]["value"] == 4
    assert data["fields"]["corners"]["status"] == "MANUAL"

    assert data["fields"]["corners"]["note"] == (
        "Manuel düzeltme"
    )


def test_low_confidence_status() -> None:
    review = create_review(
        review_id="match-1",
        source_type="OCR",
        source_file="stats.jpg",
        values={
            "shots": 14,
            "possession": 47,
        },
        confidence={
            "shots": 0.95,
            "possession": 0.50,
        },
    )

    assert review.review_status() == (
        "LOW_CONFIDENCE_REVIEW_REQUIRED"
    )


def test_auto_and_manual_counts() -> None:
    review = create_review(
        review_id="match-1",
        source_type="OCR",
        source_file="stats.jpg",
        values={
            "shots": 14,
            "corners": 3,
            "possession": 47,
        },
    )

    assert review.auto_field_count == 3
    assert review.manual_field_count == 0

    update_review_field(
        review,
        "corners",
        4,
    )

    assert review.auto_field_count == 2
    assert review.manual_field_count == 1
