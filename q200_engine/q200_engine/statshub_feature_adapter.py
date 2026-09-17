"""
Q200 Engine - StatsHub Feature Adapter

Q200 V3.1

Onaylanmış StatsHub DataReview çıktılarındaki AVG/FOR/AGT
alanlarını Home/Away Feature Engine girişine dönüştürür.

Kural:

    HOME review -> FOR -> home_* feature
    AWAY review -> FOR -> away_* feature

AVG ve AGT değerleri Home/Away takım değeri olarak tahmin edilmez.

Bu katman:
- Q200 lambda hesabı yapmaz.
- Q200 modelini çalıştırmaz.
- Odds kullanmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
- Mevcut Q200 V3.1 lambda formülünü değiştirmez.
"""

from __future__ import annotations

from typing import Any

from .data_review import DataReview
from .feature_engine import (
    FeatureSet,
    build_features,
)
from .ingestion.models import (
    MatchInfo,
    StatsHubData,
)
from .statshub_review_mapper import (
    review_to_statshub_data,
)


STATSHUB_FEATURE_ADAPTER_VERSION = (
    "Q200-STATSHUB-FEATURE-ADAPTER-V1"
)


# =========================================================
# STATSHUB FOR -> FEATURE MAPPING
# =========================================================

# StatsHub canonical base field -> Feature Engine base field.
#
# Yalnızca FOR kullanılır.
#
# AVG:
#   Genel istatistik ortalaması.
#
# AGT:
#   Takımın karşı taraf / against değeri.
#
# FOR:
#   Takımın kendi ürettiği değerdir.
#
# Bu nedenle Home/Away Feature Engine için
# FOR sütunu kullanılır.

STATSHUB_FOR_TO_FEATURE: dict[str, str] = {
    "goals": "goals",
    "xg": "xg",
    "total_shots": "total_shots",
    "shots_on_target": "shots_on_target",
    "shots_in_box": "shots_in_box",
    "shots_outside_box": "shots_outside_box",
    "possession": "possession",
    "corners": "corners",
    "big_chance_created": "big_chance_created",
    "big_chance_scored": "big_chance_scored",
    "big_chance_missed": "big_chance_missed",
    "passes": "passes",
    "touches_in_opp_box": "touches_in_opp_box",
}


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _for_values(
    data: StatsHubData,
) -> dict[str, Any]:
    """
    StatsHubData içinden yalnızca *_for alanlarını çıkarır.

    Örnek:

        xg_avg
        xg_for
        xg_agt

    içinden yalnızca:

        xg_for

    alınır.
    """

    if not isinstance(
        data,
        StatsHubData,
    ):
        raise TypeError(
            "data StatsHubData olmalıdır."
        )

    values: dict[str, Any] = {}

    for (
        source_name,
        feature_name,
    ) in STATSHUB_FOR_TO_FEATURE.items():

        source_key = (
            f"{source_name}_for"
        )

        if (
            source_key in data.values
            and data.values[source_key]
            is not None
        ):
            values[
                feature_name
            ] = data.values[source_key]

    return values


# =========================================================
# HOME + AWAY -> FEATURE INPUT
# =========================================================

def statshub_pair_to_feature_input(
    home: StatsHubData,
    away: StatsHubData,
) -> dict[str, Any]:
    """
    Home ve Away StatsHubData'yı
    Feature Engine input'una dönüştürür.

    Home:

        xg_for
        shots_for
        corners_for
        ...

    ->

        home_xg
        home_total_shots
        home_corners
        ...

    Away:

        xg_for
        shots_for
        corners_for
        ...

    ->

        away_xg
        away_total_shots
        away_corners
        ...

    AVG ve AGT değerleri aktarılmaz.
    """

    if not isinstance(
        home,
        StatsHubData,
    ):
        raise TypeError(
            "home StatsHubData olmalıdır."
        )

    if not isinstance(
        away,
        StatsHubData,
    ):
        raise TypeError(
            "away StatsHubData olmalıdır."
        )

    home_values = _for_values(
        home
    )

    away_values = _for_values(
        away
    )

    result: dict[str, Any] = {}

    for (
        name,
        value,
    ) in home_values.items():

        result[
            f"home_{name}"
        ] = value

    for (
        name,
        value,
    ) in away_values.items():

        result[
            f"away_{name}"
        ] = value

    return result


# =========================================================
# DIRECT FEATURE BUILD
# =========================================================

def build_features_from_statshub_pair(
    home: StatsHubData,
    away: StatsHubData,
) -> FeatureSet:
    """
    İki StatsHubData kaynağından doğrudan FeatureSet üretir.

    Akış:

        HOME StatsHubData
                 +
        AWAY StatsHubData
                 ↓
        statshub_pair_to_feature_input
                 ↓
        Feature Engine
                 ↓
        FeatureSet
    """

    feature_input = (
        statshub_pair_to_feature_input(
            home,
            away,
        )
    )

    return build_features(
        feature_input
    )


# =========================================================
# REVIEW -> STATSHUB DATA
# =========================================================

def _approved_review_to_data(
    review: DataReview,
    *,
    match: MatchInfo | None = None,
) -> StatsHubData:
    """
    DataReview -> StatsHubData.

    Onay kontrolü statshub_review_mapper
    katmanında yapılır.
    """

    return review_to_statshub_data(
        review,
        match=match,
    )


# =========================================================
# APPROVED REVIEWS -> FEATURES
# =========================================================

def build_features_from_approved_reviews(
    home_review: DataReview,
    away_review: DataReview,
    *,
    match: MatchInfo | None = None,
) -> FeatureSet:
    """
    Onaylanmış Home/Away DataReview'lardan
    FeatureSet üretir.

    Akış:

        HOME REVIEW
              ↓
        APPROVAL CHECK
              ↓
        StatsHubData
              │
              │
              ├──────────────┐
              │              │
              ↓              ↓
        HOME FOR       AWAY FOR
              │              │
              └──────┬───────┘
                     ↓
               Feature Engine
                     ↓
                 FeatureSet

    Onaysız review ingestion'a geçemez.

    Manuel düzeltmeler:

        review.fields[field].value

    üzerinden alınır.

    İlk OCR değerleri:

        review.fields[field].raw_value

    mapper metadata'sında korunur.
    """

    if not isinstance(
        home_review,
        DataReview,
    ):
        raise TypeError(
            "home_review DataReview olmalıdır."
        )

    if not isinstance(
        away_review,
        DataReview,
    ):
        raise TypeError(
            "away_review DataReview olmalıdır."
        )

    home = _approved_review_to_data(
        home_review,
        match=match,
    )

    away = _approved_review_to_data(
        away_review,
        match=match,
    )

    return build_features_from_statshub_pair(
        home,
        away,
    )


__all__ = [
    "STATSHUB_FEATURE_ADAPTER_VERSION",
    "STATSHUB_FOR_TO_FEATURE",
    "statshub_pair_to_feature_input",
    "build_features_from_statshub_pair",
    "build_features_from_approved_reviews",
]
