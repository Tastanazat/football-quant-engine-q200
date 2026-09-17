from __future__ import annotations

from dataclasses import dataclass

import pytest

from q200_engine.feature_selection import (
    DEFAULT_MAX_MISSING_RATE,
    DEFAULT_REDUNDANCY_CORRELATION,
    FEATURE_SELECTION_VERSION,
    FeatureSelectionReport,
    feature_selection_summary,
    feature_selection_to_dict,
    select_features,
    selected_feature_names,
)


@dataclass(frozen=True)
class Quality:
    feature_name: str
    observation_count: int
    valid_count: int
    missing_count: int
    completeness: float
    mean: float
    minimum: float
    maximum: float
    variance: float
    constant: bool


@dataclass(frozen=True)
class Pair:
    feature_a: str
    feature_b: str
    correlation: float
    absolute_correlation: float
    redundant: bool = True


@dataclass(frozen=True)
class QualityReport:
    observation_count: int
    feature_count: int
    features: tuple[Quality, ...]
    correlations: tuple[Pair, ...]
    redundant_pairs: tuple[tuple[str, str], ...] = ()


def make_quality_report():
    features = (
        Quality(
            feature_name="shots",
            observation_count=10,
            valid_count=10,
            missing_count=0,
            completeness=1.0,
            mean=20.0,
            minimum=10.0,
            maximum=30.0,
            variance=10.0,
            constant=False,
        ),
        Quality(
            feature_name="corners",
            observation_count=10,
            valid_count=8,
            missing_count=2,
            completeness=0.8,
            mean=5.0,
            minimum=2.0,
            maximum=9.0,
            variance=3.0,
            constant=False,
        ),
        Quality(
            feature_name="constant_feature",
            observation_count=10,
            valid_count=10,
            missing_count=0,
            completeness=1.0,
            mean=5.0,
            minimum=5.0,
            maximum=5.0,
            variance=0.0,
            constant=True,
        ),
        Quality(
            feature_name="bad_feature",
            observation_count=10,
            valid_count=4,
            missing_count=6,
            completeness=0.4,
            mean=1.0,
            minimum=0.0,
            maximum=2.0,
            variance=1.0,
            constant=False,
        ),
    )

    correlations = (
        Pair(
            feature_a="shots",
            feature_b="shots_on_target",
            correlation=0.91,
            absolute_correlation=0.91,
        ),
        Pair(
            feature_a="corners",
            feature_b="possession",
            correlation=0.40,
            absolute_correlation=0.40,
            redundant=False,
        ),
    )

    return QualityReport(
        observation_count=10,
        feature_count=len(features),
        features=features,
        correlations=correlations,
    )


def test_default_thresholds():
    assert DEFAULT_MAX_MISSING_RATE == 0.50
    assert DEFAULT_REDUNDANCY_CORRELATION == 0.85


def test_selection_report_version():
    report = select_features(make_quality_report())

    assert report.version == FEATURE_SELECTION_VERSION
    assert isinstance(report, FeatureSelectionReport)


def test_good_feature_is_keep():
    report = select_features(make_quality_report())

    decisions = {
        item.feature_name: item
        for item in report.decisions
    }

    assert decisions["shots"].decision == "REDUNDANT"


def test_constant_feature_is_flagged():
    report = select_features(make_quality_report())

    decisions = {
        item.feature_name: item
        for item in report.decisions
    }

    assert decisions["constant_feature"].decision == "FLAG"
    assert "CONSTANT_FEATURE" in decisions["constant_feature"].reasons


def test_high_missing_feature_is_excluded():
    report = select_features(make_quality_report())

    decisions = {
        item.feature_name: item
        for item in report.decisions
    }

    assert decisions["bad_feature"].decision == "EXCLUDE"
    assert "HIGH_MISSING_RATE" in decisions["bad_feature"].reasons


def test_partial_missing_feature_is_flagged():
    report = select_features(make_quality_report())

    decisions = {
        item.feature_name: item
        for item in report.decisions
    }

    assert decisions["corners"].decision == "FLAG"
    assert "PARTIAL_MISSING_DATA" in decisions["corners"].reasons


def test_high_correlation_creates_redundancy():
    report = select_features(make_quality_report())

    assert ("shots", "shots_on_target") in report.redundant_pairs


def test_redundancy_does_not_delete_feature():
    report = select_features(make_quality_report())

    names = {
        item.feature_name
        for item in report.decisions
    }

    assert "shots" in names
    assert "shots_on_target" in names


def test_selected_names_default_only_keep():
    report = select_features(make_quality_report())

    names = selected_feature_names(report)

    assert names == ()


def test_selected_names_can_include_flagged():
    report = select_features(make_quality_report())

    names = selected_feature_names(
        report,
        include_flagged=True,
    )

    assert "corners" in names
    assert "constant_feature" in names
    assert "bad_feature" not in names


def test_summary():
    report = select_features(make_quality_report())

    summary = feature_selection_summary(report)

    assert summary["KEEP"] == 0
    assert summary["FLAG"] == 2
    assert summary["REDUNDANT"] == 2
    assert summary["EXCLUDE"] == 1


def test_serialization():
    report = select_features(make_quality_report())

    data = feature_selection_to_dict(report)

    assert data["version"] == FEATURE_SELECTION_VERSION
    assert isinstance(data["decisions"], list)
    assert isinstance(data["redundant_pairs"], list)


def test_threshold_validation():
    with pytest.raises(ValueError):
        select_features(
            make_quality_report(),
            max_missing_rate=1.5,
        )

    with pytest.raises(ValueError):
        select_features(
            make_quality_report(),
            redundancy_correlation=-0.1,
        )


def test_empty_report_is_safe():
    report = QualityReport(
        observation_count=0,
        feature_count=0,
        features=(),
        correlations=(),
    )

    result = select_features(report)

    assert result.feature_count == 0
    assert result.decisions == ()
    assert result.redundant_pairs == ()


def test_mapping_based_report_is_supported():
    report = {
        "observation_count": 2,
        "feature_count": 1,
        "features": [
            {
                "feature_name": "possession",
                "observation_count": 2,
                "valid_count": 2,
                "missing_count": 0,
                "completeness": 1.0,
                "constant": False,
            }
        ],
        "correlations": {},
    }

    result = select_features(report)

    assert result.feature_count == 1
    assert result.decisions[0].feature_name == "possession"
    assert result.decisions[0].decision == "KEEP"
