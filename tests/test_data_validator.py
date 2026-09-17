from __future__ import annotations

import math

import pytest

from q200_engine.ingestion.data_validator import (
    DATA_VALIDATOR_VERSION,
    validate_canonical_values,
)


REQUIRED = (
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
)


def valid_values():
    return {
        "home_gf_per_match": 1.5,
        "home_ga_per_match": 1.0,
        "away_gf_per_match": 1.2,
        "away_ga_per_match": 1.4,
        "home_corners_for": 5.0,
        "away_corners_for": 4.0,
        "home_scoring_rate": 75.0,
        "away_scoring_rate": 50.0,
        "possession": 55.0,
    }


def test_validator_version():
    report = validate_canonical_values(
        valid_values(),
        required_fields=REQUIRED,
    )

    assert (
        report.validator_version
        == DATA_VALIDATOR_VERSION
    )


def test_valid_data_passes():
    report = validate_canonical_values(
        valid_values(),
        required_fields=REQUIRED,
    )

    assert report.valid is True
    assert report.error_count == 0
    assert report.missing_fields == []


def test_missing_required_field_fails():
    values = valid_values()
    del values["away_ga_per_match"]

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        "away_ga_per_match"
        in report.missing_fields
    )


def test_negative_value_fails():
    values = valid_values()
    values["home_corners_for"] = -1

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert report.issues[0].code == "NEGATIVE"


def test_percentage_above_100_fails():
    values = valid_values()
    values["home_scoring_rate"] = 101

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "PERCENTAGE_RANGE"
    )


def test_percentage_below_zero_fails():
    values = valid_values()
    values["away_scoring_rate"] = -1

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert report.issues[0].code == "NEGATIVE"


def test_nan_fails():
    values = valid_values()
    values["home_gf_per_match"] = math.nan

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "NON_FINITE"
    )


def test_infinity_fails():
    values = valid_values()
    values["home_gf_per_match"] = math.inf

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "NON_FINITE"
    )


def test_string_number_fails_instead_of_being_guessed():
    values = valid_values()
    values["home_gf_per_match"] = "1.50"

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "NON_NUMERIC"
    )


def test_boolean_is_not_accepted_as_number():
    values = valid_values()
    values["home_gf_per_match"] = True

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "NON_NUMERIC"
    )


def test_none_is_allowed_for_optional_field():
    values = valid_values()
    values["home_corners_for"] = None

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is True


def test_goal_minute_above_130_fails():
    values = valid_values()
    values[
        "home_average_goal_minute_for"
    ] = 131

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.valid is False
    assert (
        report.issues[0].code
        == "MINUTE_RANGE"
    )


def test_custom_required_fields_are_supported():
    values = {
        "shots": 25.0,
        "possession": 55.0,
    }

    report = validate_canonical_values(
        values,
        required_fields=(
            "shots",
            "possession",
        ),
    )

    assert report.valid is True
    assert report.error_count == 0


def test_invalid_values_type_raises():
    with pytest.raises(TypeError):
        validate_canonical_values(
            [],  # type: ignore[arg-type]
            required_fields=REQUIRED,
        )


def test_validation_report_contains_error_details():
    values = valid_values()
    values["home_corners_for"] = -3

    report = validate_canonical_values(
        values,
        required_fields=REQUIRED,
    )

    assert report.error_count == 1

    issue = report.issues[0]

    assert issue.field == "home_corners_for"
    assert issue.value == -3
    assert issue.code == "NEGATIVE"
    assert "negatif" in issue.message
