from __future__ import annotations

import pytest

from q200_engine.feature_quality import (
    build_feature_quality_report,
)

from q200_engine.feature_selection import (
    DEFAULT_MISSINGNESS_THRESHOLD,
    FEATURE_SELECTION_VERSION,
    FeatureSelectionReport,
    build_feature_selection,
    feature_selection_to_dict,
    filter_feature_mapping,
    review_feature_names,
    selected_feature_names,
)


def _quality_report():
    rows = [
        {
            "goals": 1.0,
            "xg": 1.10,
            "shots": 10.0,
            "possession": 55.0,
        },
        {
            "goals": 2.0,
            "xg": 2.40,
            "shots": 21.0,
            "possession": 42.0,
        },
        {
            "goals": 0.0,
            "xg": 0.60,
            "shots": 7.0,
            "possession": 63.0,
        },
        {
            "goals": 3.0,
            "xg": 1.70,
            "shots": 18.0,
            "possession": 49.0,
        },
        {
            "goals": 1.0,
            "xg": 2.10,
            "shots": 13.0,
            "possession": 58.0,
        },
        {
            "goals": 2.0,
            "xg": 0.90,
            "shots": 26.0,
            "possession": 37.0,
        },
        {
            "goals": 4.0,
            "xg": 1.30,
            "shots": 9.0,
            "possession": 67.0,
        },
        {
            "goals": 0.0,
            "xg": 2.70,
            "shots": 24.0,
            "possession": 44.0,
        },
        {
            "goals": 3.0,
            "xg": 0.80,
            "shots": 15.0,
            "possession": 52.0,
        },
        {
            "goals": 1.0,
            "xg": 1.90,
            "shots": 28.0,
            "possession": 41.0,
        },
    ]

    return build_feature_quality_report(
        rows,
        threshold=0.85,
    )


def test_feature_selection_version():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    assert (
        selection.version
        == FEATURE_SELECTION_VERSION
    )


def test_feature_selection_returns_report():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    assert isinstance(
        selection,
        FeatureSelectionReport,
    )


def test_clean_features_are_kept():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    assert (
        "goals"
        in selected_feature_names(selection)
    )


def test_selection_counts_match_decisions():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    total = (
        len(selection.selected_features)
        + len(selection.review_features)
        + len(selection.excluded_features)
    )

    assert (
        total
        == selection.feature_count
    )


def test_selection_does_not_automatically_exclude_features():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    assert (
        selection.excluded_features
        == ()
    )


def test_mapping_filter_keeps_selected_features():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    values = {
        feature_name: 1.0
        for feature_name in report.features
    }

    filtered = filter_feature_mapping(
        values,
        selection,
    )

    assert set(filtered).issubset(
        set(selection.selected_features)
    )


def test_mapping_can_include_review_features():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    values = {
        feature_name: 1.0
        for feature_name in report.features
    }

    filtered = filter_feature_mapping(
        values,
        selection,
        include_review=True,
    )

    assert set(filtered).issubset(
        set(selection.selected_features)
        | set(selection.review_features)
    )


def test_selection_to_dict():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    data = feature_selection_to_dict(
        selection
    )

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["version"]
        == FEATURE_SELECTION_VERSION
    )

    assert "decisions" in data

    assert "selected_features" in data


def test_review_features_are_accessible():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    assert isinstance(
        review_feature_names(selection),
        tuple,
    )


def test_missingness_threshold_validation():
    report = _quality_report()

    with pytest.raises(
        ValueError
    ):
        build_feature_selection(
            report,
            missingness_threshold=1.5,
        )


def test_correlation_threshold_validation():
    report = _quality_report()

    with pytest.raises(
        ValueError
    ):
        build_feature_selection(
            report,
            correlation_threshold=-0.1,
        )


def test_default_missingness_threshold():
    assert (
        DEFAULT_MISSINGNESS_THRESHOLD
        == 0.50
    )


def test_invalid_report_type():
    with pytest.raises(
        TypeError
    ):
        build_feature_selection(
            "invalid"
        )


def test_invalid_mapping_type():
    report = _quality_report()

    selection = build_feature_selection(
        report
    )

    with pytest.raises(
        TypeError
    ):
        filter_feature_mapping(
            [],
            selection,
        )
