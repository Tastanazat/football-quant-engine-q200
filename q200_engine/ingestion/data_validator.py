"""
Q200 Engine - Canonical Data Validator

Q200 V3.1

Canonical Data
      ↓
Validation
      ↓
Validated Canonical Data

Bu katman:
- Canonical veriyi kontrol eder.
- Geçersiz sayısal değerleri yakalar.
- Possession sınırlarını kontrol eder.
- Negatif değerleri yakalar.
- Eksik alanları raporlar.
- Kaynak bilgisini değiştirmez.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds kullanmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .models import CanonicalMatchData


DATA_VALIDATOR_VERSION = "Q200-DATA-VALIDATOR-V1"


DEFAULT_REQUIRED_FIELDS = (
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
)


PERCENTAGE_FIELDS = {
    "home_scoring_rate",
    "away_scoring_rate",
    "home_conceding_rate",
    "away_conceding_rate",
    "over_1_5",
    "over_2_5",
    "over_3_5",
    "btts",
    "h2h_home_scored_rate",
    "h2h_away_scored_rate",
    "h2h_btts_rate",
    "h2h_over_1_5",
    "h2h_over_2_5",
    "h2h_over_3_5",
    "home_points_percentage",
    "away_points_percentage",
    "home_goals_percentage",
    "away_goals_percentage",
    "home_goals_conceded_percentage",
    "away_goals_conceded_percentage",
}


NON_NEGATIVE_FIELDS = {
    "home_gf",
    "home_ga",
    "away_gf",
    "away_ga",
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
    "home_corners_for",
    "home_corners_against",
    "away_corners_for",
    "away_corners_against",
    "home_total_corners",
    "away_total_corners",
    "home_ppg",
    "away_ppg",
    "h2h_matches",
    "h2h_home_wins",
    "h2h_draws",
    "h2h_away_wins",
    "h2h_home_goals",
    "h2h_away_goals",
    "h2h_home_goals_per_match",
    "h2h_away_goals_per_match",
    "h2h_total_goals_per_match",
    "home_average_goal_minute_for",
    "away_average_goal_minute_for",
    "home_average_goal_minute_against",
    "away_average_goal_minute_against",
}


@dataclass(frozen=True)
class ValidationIssue:
    """Tek bir validation problemi."""

    field: str
    value: Any
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Canonical data validation sonucu."""

    validator_version: str
    valid: bool
    checked_fields: int
    valid_fields: int
    missing_fields: list[str] = field(
        default_factory=list
    )
    issues: list[ValidationIssue] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def error_count(self) -> int:
        return len(self.issues)


def _is_number(value: Any) -> bool:
    """
    Bool değerleri sayı olarak kabul etmez.
    """

    if isinstance(value, bool):
        return False

    return isinstance(
        value,
        (int, float),
    )


def _is_finite(value: Any) -> bool:
    if not _is_number(value):
        return False

    return math.isfinite(float(value))


def _validate_value(
    field_name: str,
    value: Any,
) -> ValidationIssue | None:

    if value is None:
        return None

    if not _is_number(value):
        return ValidationIssue(
            field=field_name,
            value=value,
            code="NON_NUMERIC",
            message=(
                f"{field_name} sayısal bir değer "
                "olmalıdır."
            ),
        )

    if not _is_finite(value):
        return ValidationIssue(
            field=field_name,
            value=value,
            code="NON_FINITE",
            message=(
                f"{field_name} finite bir sayı "
                "olmalıdır."
            ),
        )

    numeric = float(value)

    if (
        field_name in NON_NEGATIVE_FIELDS
        and numeric < 0
    ):
        return ValidationIssue(
            field=field_name,
            value=value,
            code="NEGATIVE",
            message=(
                f"{field_name} negatif olamaz."
            ),
        )

    if (
        field_name in PERCENTAGE_FIELDS
        and not 0.0 <= numeric <= 100.0
    ):
        return ValidationIssue(
            field=field_name,
            value=value,
            code="PERCENTAGE_RANGE",
            message=(
                f"{field_name} 0 ile 100 "
                "arasında olmalıdır."
            ),
        )

    if (
        field_name
        in {
            "home_average_goal_minute_for",
            "away_average_goal_minute_for",
            "home_average_goal_minute_against",
            "away_average_goal_minute_against",
        }
        and numeric > 130
    ):
        return ValidationIssue(
            field=field_name,
            value=value,
            code="MINUTE_RANGE",
            message=(
                f"{field_name} gerçekçi bir "
                "maç dakikası aralığında olmalıdır."
            ),
        )

    return None


def validate_canonical_values(
    values: dict[str, Any],
    *,
    required_fields: tuple[str, ...] = DEFAULT_REQUIRED_FIELDS,
) -> ValidationReport:
    """
    Canonical value sözlüğünü validate eder.
    """

    if not isinstance(values, dict):
        raise TypeError(
            "values dict olmalıdır."
        )

    if not isinstance(
        required_fields,
        tuple,
    ):
        raise TypeError(
            "required_fields tuple olmalıdır."
        )

    issues: list[ValidationIssue] = []
    missing_fields: list[str] = []
    checked_fields = 0
    valid_fields = 0

    for field_name in required_fields:

        if field_name not in values:
            missing_fields.append(
                field_name
            )

    for field_name, value in values.items():

        checked_fields += 1

        issue = _validate_value(
            field_name,
            value,
        )

        if issue is not None:
            issues.append(issue)
        else:
            valid_fields += 1

    warnings: list[str] = []

    if missing_fields:
        warnings.append(
            "Required canonical alanların "
            f"{len(missing_fields)} tanesi eksik."
        )

    valid = (
        not issues
        and not missing_fields
    )

    return ValidationReport(
        validator_version=(
            DATA_VALIDATOR_VERSION
        ),
        valid=valid,
        checked_fields=checked_fields,
        valid_fields=valid_fields,
        missing_fields=missing_fields,
        issues=issues,
        warnings=warnings,
    )


def validate_canonical_data(
    data: CanonicalMatchData,
    *,
    required_fields: tuple[str, ...] = DEFAULT_REQUIRED_FIELDS,
) -> ValidationReport:
    """
    CanonicalMatchData nesnesini validate eder.
    """

    if not isinstance(
        data,
        CanonicalMatchData,
    ):
        raise TypeError(
            "data CanonicalMatchData olmalıdır."
        )

    return validate_canonical_values(
        data.canonical_values,
        required_fields=required_fields,
    )


def validation_to_dict(
    report: ValidationReport,
) -> dict[str, Any]:
    """
    ValidationReport'u JSON uyumlu dict'e çevirir.
    """

    if not isinstance(
        report,
        ValidationReport,
    ):
        raise TypeError(
            "report ValidationReport olmalıdır."
        )

    return {
        "validator_version": (
            report.validator_version
        ),
        "valid": report.valid,
        "checked_fields": (
            report.checked_fields
        ),
        "valid_fields": (
            report.valid_fields
        ),
        "missing_fields": list(
            report.missing_fields
        ),
        "issues": [
            {
                "field": issue.field,
                "value": issue.value,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in report.issues
        ],
        "warnings": list(
            report.warnings
        ),
        "error_count": (
            report.error_count
        ),
    }


__all__ = [
    "DATA_VALIDATOR_VERSION",
    "DEFAULT_REQUIRED_FIELDS",
    "ValidationIssue",
    "ValidationReport",
    "validate_canonical_values",
    "validate_canonical_data",
    "validation_to_dict",
]
