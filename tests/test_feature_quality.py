from __future__ import annotations

import pytest

from q200_engine.feature_quality import (
    DEFAULT_CORRELATION_THRESHOLD,
    FEATURE_QUALITY_VERSION,
    FeatureQualityReport,
    assess_feature_quality,
    build_feature_quality_report,
    calculate_all_correlations,
    calculate_feature_correlation,
    discover_features,
    feature_quality_to_dict,
    find_redundant_features,
)


def _dataset() -> list[dict[str, float]]:
    return [
        {
            "total_shots": 10,
            "shots_on_target": 5,
            "xg": 1.0,
            "possession": 40,
            "corners": 3,
        },
        {
            "total_shots": 20,
            "shots_on_target": 10,
            "xg": 2.0,
            "possession": 50,
            "corners": 6,
        },
        {
            "total_shots": 30,
            "shots_on_target": 15,
            "xg": 3.0,
            "possession": 60,
            "corners": 9,
        },
        {
            "total_shots": 40,
            "shots_on_target": 20,
            "xg": 4.0,
            "possession": 70,
            "corners": 12,
        },
    ]


def test_discover_features_is_deterministic() -> None:
    result = discover_features(
        _dataset()
    )

    assert result == sorted(
        [
            "total_shots",
            "shots_on_target",
            "xg",
            "possession",
            "corners",
        ]
    )


def test_feature_quality_counts_missing_values() -> None:
    dataset = [
        {
            "shots": 10,
        },
        {
            "shots": 20,
        },
        {
            "shots": None,
        },
        {
            "shots": 40,
        },
    ]

    result = assess_feature_quality(
        dataset
    )

    quality = result["shots"]

    assert quality.observation_count == 4
    assert quality.valid_count == 3
    assert quality.missing_count == 1
    assert quality.completeness == pytest.approx(
        0.75
    )


def test_feature_quality_calculates_statistics() -> None:
    result = assess_feature_quality(
        _dataset()
    )

    quality = result["total_shots"]

    assert quality.mean == pytest.approx(
        25.0
    )

    assert quality.minimum == 10
    assert quality.maximum == 40

    assert quality.variance == pytest.approx(
        125.0
    )

    assert quality.constant is False


def test_constant_feature_is_detected() -> None:
    dataset = [
        {"possession": 50},
        {"possession": 50},
        {"possession": 50},
        {"possession": 50},
    ]

    result = assess_feature_quality(
        dataset
    )

    assert (
        result["possession"].constant
        is True
    )

    assert (
        result["possession"].variance
        == pytest.approx(0.0)
    )


def test_perfect_positive_correlation() -> None:
    correlation = (
        calculate_feature_correlation(
            _dataset(),
            "total_shots",
            "shots_on_target",
        )
    )

    assert correlation == pytest.approx(
        1.0
    )


def test_perfect_negative_correlation() -> None:
    dataset = [
        {
            "a": 1,
            "b": 10,
        },
        {
            "a": 2,
            "b": 8,
        },
        {
            "a": 3,
            "b": 6,
        },
        {
            "a": 4,
            "b": 4,
        },
    ]

    correlation = (
        calculate_feature_correlation(
            dataset,
            "a",
            "b",
        )
    )

    assert correlation == pytest.approx(
        -1.0
    )


def test_missing_values_are_pairwise_ignored() -> None:
    dataset = [
        {
            "a": 1,
            "b": 2,
        },
        {
            "a": 2,
            "b": 4,
        },
        {
            "a": 3,
            "b": None,
        },
        {
            "a": None,
            "b": 8,
        },
        {
            "a": 5,
            "b": 10,
        },
    ]

    correlation = (
        calculate_feature_correlation(
            dataset,
            "a",
            "b",
        )
    )

    assert correlation == pytest.approx(
        1.0
    )


def test_constant_feature_has_no_correlation() -> None:
    dataset = [
        {
            "a": 5,
            "b": 1,
        },
        {
            "a": 5,
            "b": 2,
        },
        {
            "a": 5,
            "b": 3,
        },
    ]

    correlation = (
        calculate_feature_correlation(
            dataset,
            "a",
            "b",
        )
    )

    assert correlation is None


def test_all_correlations_do_not_duplicate_pairs() -> None:
    result = calculate_all_correlations(
        _dataset()
    )

    pairs = {
        (
            pair.feature_a,
            pair.feature_b,
        )
        for pair in result
    }

    assert len(pairs) == len(result)

    for feature_a, feature_b in pairs:
        assert feature_a < feature_b


def test_redundant_features_are_detected() -> None:
    result = find_redundant_features(
        _dataset(),
        threshold=0.95,
    )

    assert result

    assert all(
        pair.redundant
        for pair in result
    )

    assert all(
        pair.absolute_correlation
        >= 0.95
        for pair in result
    )


def test_redundant_pairs_are_sorted_by_strength() -> None:
    result = find_redundant_features(
        _dataset(),
        threshold=0.50,
    )

    absolute_values = [
        pair.absolute_correlation
        for pair in result
    ]

    assert absolute_values == sorted(
        absolute_values,
        reverse=True,
    )


def test_default_threshold_is_defined() -> None:
    assert (
        DEFAULT_CORRELATION_THRESHOLD
        == pytest.approx(0.85)
    )


def test_complete_quality_report() -> None:
    report = build_feature_quality_report(
        _dataset()
    )

    assert isinstance(
        report,
        FeatureQualityReport,
    )

    assert (
        report.version
        == FEATURE_QUALITY_VERSION
    )

    assert (
        report.observation_count
        == 4
    )

    assert (
        report.feature_count
        == 5
    )

    assert report.correlations

    assert report.redundant_pairs


def test_quality_report_to_dict() -> None:
    report = build_feature_quality_report(
        _dataset()
    )

    data = feature_quality_to_dict(
        report
    )

    assert (
        data["version"]
        == FEATURE_QUALITY_VERSION
    )

    assert (
        data["observation_count"]
        == 4
    )

    assert (
        "features"
        in data
    )

    assert (
        "correlations"
        in data
    )

    assert (
        "redundant_pairs"
        in data
    )


def test_threshold_must_be_between_zero_and_one() -> None:
    with pytest.raises(
        ValueError,
        match="0 ile 1",
    ):
        find_redundant_features(
            _dataset(),
            threshold=1.5,
        )


def test_threshold_cannot_be_boolean() -> None:
    with pytest.raises(
        TypeError,
        match="boolean",
    ):
        find_redundant_features(
            _dataset(),
            threshold=True,
        )


def test_invalid_observation_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="mapping",
    ):
        build_feature_quality_report(
            [1, 2, 3]
        )


def test_empty_dataset_is_safe() -> None:
    report = build_feature_quality_report(
        []
    )

    assert report.observation_count == 0
    assert report.feature_count == 0
    assert report.correlations == []
    assert report.redundant_pairs == []
