from __future__ import annotations

import pytest

from q200_engine.feature_engine import (
    FEATURE_ENGINE_VERSION,
    FeatureSet,
    build_features,
    feature_set_to_dict,
)


def test_feature_engine_builds_shot_features() -> None:
    features = build_features(
        {
            "home_total_shots": 20,
            "away_total_shots": 10,
            "home_shots_on_target": 8,
            "away_shots_on_target": 3,
            "home_shots_in_box": 12,
            "away_shots_in_box": 5,
            "home_shots_outside_box": 8,
            "away_shots_outside_box": 5,
            "home_xg": 2.0,
            "away_xg": 0.8,
        }
    )

    assert isinstance(
        features,
        FeatureSet,
    )

    assert (
        features.feature_engine_version
        == FEATURE_ENGINE_VERSION
    )

    assert (
        features.home_shot_accuracy
        == pytest.approx(0.40)
    )

    assert (
        features.away_shot_accuracy
        == pytest.approx(0.30)
    )

    assert (
        features.home_xg_per_shot
        == pytest.approx(0.10)
    )

    assert (
        features.away_xg_per_shot
        == pytest.approx(0.08)
    )

    assert (
        features.home_shots_in_box_ratio
        == pytest.approx(0.60)
    )

    assert (
        features.away_shots_in_box_ratio
        == pytest.approx(0.50)
    )

    assert (
        features.shot_differential
        == pytest.approx(10.0)
    )

    assert (
        features.shots_on_target_differential
        == pytest.approx(5.0)
    )

    assert (
        features.xg_differential
        == pytest.approx(1.2)
    )


def test_feature_engine_builds_possession_features() -> None:
    features = build_features(
        {
            "home_total_shots": 20,
            "away_total_shots": 10,
            "home_xg": 2.0,
            "away_xg": 0.8,
            "home_possession": 60,
            "away_possession": 40,
        }
    )

    assert (
        features.possession_differential
        == pytest.approx(20.0)
    )

    assert (
        features.home_shots_per_possession_point
        == pytest.approx(
            20 / 60
        )
    )

    assert (
        features.away_shots_per_possession_point
        == pytest.approx(
            10 / 40
        )
    )

    assert (
        features.home_xg_per_possession_point
        == pytest.approx(
            2 / 60
        )
    )

    assert (
        features.away_xg_per_possession_point
        == pytest.approx(
            0.8 / 40
        )
    )


def test_feature_engine_builds_corner_features() -> None:
    features = build_features(
        {
            "home_corners": 7,
            "away_corners": 4,
        }
    )

    assert (
        features.home_corners
        == 7
    )

    assert (
        features.away_corners
        == 4
    )

    assert (
        features.corner_differential
        == pytest.approx(3)
    )

    assert (
        features.total_corners
        == pytest.approx(11)
    )


def test_feature_engine_builds_big_chance_features() -> None:
    features = build_features(
        {
            "home_big_chance_created": 5,
            "away_big_chance_created": 2,
            "home_big_chance_scored": 3,
            "away_big_chance_scored": 1,
            "home_big_chance_missed": 2,
            "away_big_chance_missed": 1,
        }
    )

    assert (
        features.home_big_chance_conversion
        == pytest.approx(0.60)
    )

    assert (
        features.away_big_chance_conversion
        == pytest.approx(0.50)
    )


def test_feature_engine_accepts_uppercase_field_names() -> None:
    features = build_features(
        {
            "HOME_TOTAL_SHOTS": 18,
            "AWAY_TOTAL_SHOTS": 12,
            "HOME_SHOTS_ON_TARGET": 7,
            "AWAY_SHOTS_ON_TARGET": 4,
        }
    )

    assert (
        features.home_total_shots
        == 18
    )

    assert (
        features.away_total_shots
        == 12
    )

    assert (
        features.home_shot_accuracy
        == pytest.approx(
            7 / 18
        )
    )


def test_feature_engine_allows_missing_optional_data() -> None:
    features = build_features(
        {
            "home_total_shots": 20,
            "away_total_shots": 10,
        }
    )

    assert (
        features.home_total_shots
        == 20
    )

    assert (
        features.away_total_shots
        == 10
    )

    assert (
        features.home_shot_accuracy
        is None
    )

    assert (
        features.away_shot_accuracy
        is None
    )

    assert (
        features.corner_differential
        is None
    )


def test_zero_denominator_returns_none() -> None:
    features = build_features(
        {
            "home_total_shots": 0,
            "away_total_shots": 10,
            "home_shots_on_target": 0,
            "away_shots_on_target": 3,
            "home_xg": 0,
            "away_xg": 1,
        }
    )

    assert (
        features.home_shot_accuracy
        is None
    )

    assert (
        features.home_xg_per_shot
        is None
    )

    assert (
        features.away_shot_accuracy
        == pytest.approx(0.30)
    )


def test_possession_cannot_exceed_100() -> None:
    with pytest.raises(
        ValueError,
        match="100",
    ):
        build_features(
            {
                "home_possession": 101,
                "away_possession": 0,
            }
        )


def test_negative_statistics_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="küçük olamaz",
    ):
        build_features(
            {
                "home_total_shots": -1,
            }
        )


def test_boolean_statistics_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="boolean",
    ):
        build_features(
            {
                "home_total_shots": True,
            }
        )


def test_feature_serialization() -> None:
    features = build_features(
        {
            "home_total_shots": 20,
            "away_total_shots": 10,
            "home_corners": 6,
            "away_corners": 4,
        }
    )

    data = feature_set_to_dict(
        features
    )

    assert (
        data["feature_engine_version"]
        == FEATURE_ENGINE_VERSION
    )

    assert (
        data["home_total_shots"]
        == 20
    )

    assert (
        data["away_total_shots"]
        == 10
    )

    assert (
        data["total_corners"]
        == 10
    )


def test_feature_completeness_is_bounded() -> None:
    features = build_features(
        {
            "home_total_shots": 20,
            "away_total_shots": 10,
            "home_shots_on_target": 5,
            "away_shots_on_target": 3,
        }
    )

    assert (
        0.0
        <= features.data_completeness
        <= 1.0
    )

    assert (
        features.available_feature_count
        > 0
    )

    assert (
        features.missing_feature_count
        > 0
    )
