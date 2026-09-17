"""
Q200 Engine - Feature Engine

Q200 V3.1

Amaç:
Ham football statistics verisini modelleme öncesi
anlamlı ve denetlenebilir özelliklere dönüştürmek.

ÖNEMLİ:
Bu katman henüz Q200 lambda hesabını değiştirmez.

Akış:

RAW STATISTICS
      ↓
DATA REVIEW
      ↓
FEATURE ENGINE
      ↓
FEATURE QUALITY
      ↓
Q200 MODEL

Desteklenen ana istatistik grupları:

- Goals
- xG
- Total Shots
- Shots On Target
- Shots In The Box
- Shots Outside The Box
- Possession
- Corners
- Big Chances
- Passes
- Touches In Opp Box

Türetilen örnek özellikler:

- shot_accuracy
- xg_per_shot
- shots_in_box_ratio
- shots_outside_box_ratio
- corner_differential
- possession_differential
- shot_differential
- shots_on_target_differential
- xg_differential
- big_chance_conversion
- shots_per_possession_point
- xg_per_possession_point

Model çekirdeği bu katmandan bağımsızdır.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping


FEATURE_ENGINE_VERSION = "Q200-FEATURE-ENGINE-V1"


# =========================================================
# VALIDATION
# =========================================================

def _number(
    value: Any,
    field_name: str,
    *,
    minimum: float = 0.0,
) -> float:
    """
    Güvenli sayısal değer doğrulaması.
    """

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} boolean olamaz."
        )

    if value is None:
        raise ValueError(
            f"{field_name} boş olamaz."
        )

    try:
        result = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} sayısal olmalıdır."
        ) from exc

    if not math.isfinite(result):
        raise ValueError(
            f"{field_name} finite bir sayı olmalıdır."
        )

    if result < minimum:
        raise ValueError(
            f"{field_name} {minimum} değerinden küçük olamaz."
        )

    return result


def _optional_number(
    data: Mapping[str, Any],
    field_name: str,
) -> float | None:
    """
    Opsiyonel alanı güvenli şekilde okur.
    """

    if field_name not in data:
        return None

    value = data[field_name]

    if value is None:
        return None

    return _number(
        value,
        field_name,
    )


def _safe_ratio(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    """
    Sıfıra bölme olmadan oran hesaplar.
    """

    if numerator is None or denominator is None:
        return None

    if denominator <= 0:
        return None

    return numerator / denominator


def _safe_difference(
    home: float | None,
    away: float | None,
) -> float | None:
    """
    Home - Away farkı.
    """

    if home is None or away is None:
        return None

    return home - away


# =========================================================
# FEATURE SET
# =========================================================

@dataclass(frozen=True)
class FeatureSet:
    """
    Q200 Feature Engine çıktısı.

    Ham değerleri değiştirmez.
    Sadece türetilmiş özellikleri taşır.
    """

    feature_engine_version: str

    # -----------------------------------------------------
    # GOALS / xG
    # -----------------------------------------------------

    home_goals: float | None = None
    away_goals: float | None = None

    home_xg: float | None = None
    away_xg: float | None = None

    xg_differential: float | None = None

    # -----------------------------------------------------
    # SHOTS
    # -----------------------------------------------------

    home_total_shots: float | None = None
    away_total_shots: float | None = None

    home_shots_on_target: float | None = None
    away_shots_on_target: float | None = None

    home_shots_in_box: float | None = None
    away_shots_in_box: float | None = None

    home_shots_outside_box: float | None = None
    away_shots_outside_box: float | None = None

    # -----------------------------------------------------
    # SHOT FEATURES
    # -----------------------------------------------------

    home_shot_accuracy: float | None = None
    away_shot_accuracy: float | None = None

    home_xg_per_shot: float | None = None
    away_xg_per_shot: float | None = None

    home_shots_in_box_ratio: float | None = None
    away_shots_in_box_ratio: float | None = None

    home_shots_outside_box_ratio: float | None = None
    away_shots_outside_box_ratio: float | None = None

    shot_differential: float | None = None

    shots_on_target_differential: float | None = None

    # -----------------------------------------------------
    # POSSESSION
    # -----------------------------------------------------

    home_possession: float | None = None
    away_possession: float | None = None

    possession_differential: float | None = None

    # -----------------------------------------------------
    # POSSESSION EFFICIENCY
    # -----------------------------------------------------

    home_shots_per_possession_point: float | None = None
    away_shots_per_possession_point: float | None = None

    home_xg_per_possession_point: float | None = None
    away_xg_per_possession_point: float | None = None

    # -----------------------------------------------------
    # CORNERS
    # -----------------------------------------------------

    home_corners: float | None = None
    away_corners: float | None = None

    corner_differential: float | None = None

    total_corners: float | None = None

    # -----------------------------------------------------
    # BIG CHANCES
    # -----------------------------------------------------

    home_big_chance_created: float | None = None
    away_big_chance_created: float | None = None

    home_big_chance_scored: float | None = None
    away_big_chance_scored: float | None = None

    home_big_chance_missed: float | None = None
    away_big_chance_missed: float | None = None

    home_big_chance_conversion: float | None = None
    away_big_chance_conversion: float | None = None

    # -----------------------------------------------------
    # PASSING / BOX TOUCHES
    # -----------------------------------------------------

    home_passes: float | None = None
    away_passes: float | None = None

    home_touches_in_opp_box: float | None = None
    away_touches_in_opp_box: float | None = None

    # -----------------------------------------------------
    # QUALITY FLAGS
    # -----------------------------------------------------

    available_feature_count: int = 0

    missing_feature_count: int = 0

    @property
    def feature_count(self) -> int:
        return (
            self.available_feature_count
            + self.missing_feature_count
        )

    @property
    def data_completeness(self) -> float:
        """
        Mevcut feature oranı.

        0.0 - 1.0
        """

        total = self.feature_count

        if total <= 0:
            return 0.0

        return (
            self.available_feature_count
            / total
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =========================================================
# POSSESSION VALIDATION
# =========================================================

def _validate_possession(
    value: float | None,
    field_name: str,
) -> float | None:
    """
    Possession yüzde değerini doğrular.

    Kabul:

        0 <= possession <= 100
    """

    if value is None:
        return None

    result = _number(
        value,
        field_name,
    )

    if result > 100:
        raise ValueError(
            f"{field_name} 100'den büyük olamaz."
        )

    return result


# =========================================================
# INPUT NORMALIZATION
# =========================================================

def normalize_feature_input(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Feature input alanlarını normalize eder.

    Field isimleri:

        HOME_TOTAL_SHOTS
        home_total_shots
        Home_Total_Shots

    → home_total_shots
    """

    if not isinstance(data, Mapping):
        raise TypeError(
            "Feature input mapping/dictionary olmalıdır."
        )

    normalized: dict[str, Any] = {}

    for key, value in data.items():

        if not isinstance(key, str):
            raise TypeError(
                "Feature field isimleri string olmalıdır."
            )

        normalized_key = (
            key.strip()
            .lower()
        )

        if not normalized_key:
            raise ValueError(
                "Boş feature field adı kullanılamaz."
            )

        normalized[
            normalized_key
        ] = value

    return normalized


# =========================================================
# BUILD FEATURES
# =========================================================

def build_features(
    data: Mapping[str, Any],
) -> FeatureSet:
    """
    Ham Home/Away statistics verisinden FeatureSet üretir.

    Beklenen örnek alanlar:

        home_total_shots
        away_total_shots

        home_shots_on_target
        away_shots_on_target

        home_xg
        away_xg

        home_possession
        away_possession

        home_corners
        away_corners

    Eksik alanlar hata oluşturmaz.
    Çünkü farklı kaynaklar farklı statistics sağlayabilir.

    Ancak mevcut alanlar mutlaka doğrulanır.
    """

    normalized = normalize_feature_input(
        data
    )

    # =====================================================
    # RAW VALUES
    # =====================================================

    home_goals = _optional_number(
        normalized,
        "home_goals",
    )

    away_goals = _optional_number(
        normalized,
        "away_goals",
    )

    home_xg = _optional_number(
        normalized,
        "home_xg",
    )

    away_xg = _optional_number(
        normalized,
        "away_xg",
    )

    home_total_shots = _optional_number(
        normalized,
        "home_total_shots",
    )

    away_total_shots = _optional_number(
        normalized,
        "away_total_shots",
    )

    home_sot = _optional_number(
        normalized,
        "home_shots_on_target",
    )

    away_sot = _optional_number(
        normalized,
        "away_shots_on_target",
    )

    home_in_box = _optional_number(
        normalized,
        "home_shots_in_box",
    )

    away_in_box = _optional_number(
        normalized,
        "away_shots_in_box",
    )

    home_outside_box = _optional_number(
        normalized,
        "home_shots_outside_box",
    )

    away_outside_box = _optional_number(
        normalized,
        "away_shots_outside_box",
    )

    home_possession = _validate_possession(
        _optional_number(
            normalized,
            "home_possession",
        ),
        "home_possession",
    )

    away_possession = _validate_possession(
        _optional_number(
            normalized,
            "away_possession",
        ),
        "away_possession",
    )

    home_corners = _optional_number(
        normalized,
        "home_corners",
    )

    away_corners = _optional_number(
        normalized,
        "away_corners",
    )

    home_big_created = _optional_number(
        normalized,
        "home_big_chance_created",
    )

    away_big_created = _optional_number(
        normalized,
        "away_big_chance_created",
    )

    home_big_scored = _optional_number(
        normalized,
        "home_big_chance_scored",
    )

    away_big_scored = _optional_number(
        normalized,
        "away_big_chance_scored",
    )

    home_big_missed = _optional_number(
        normalized,
        "home_big_chance_missed",
    )

    away_big_missed = _optional_number(
        normalized,
        "away_big_chance_missed",
    )

    home_passes = _optional_number(
        normalized,
        "home_passes",
    )

    away_passes = _optional_number(
        normalized,
        "away_passes",
    )

    home_touches = _optional_number(
        normalized,
        "home_touches_in_opp_box",
    )

    away_touches = _optional_number(
        normalized,
        "away_touches_in_opp_box",
    )

    # =====================================================
    # DERIVED FEATURES
    # =====================================================

    home_shot_accuracy = _safe_ratio(
        home_sot,
        home_total_shots,
    )

    away_shot_accuracy = _safe_ratio(
        away_sot,
        away_total_shots,
    )

    home_xg_per_shot = _safe_ratio(
        home_xg,
        home_total_shots,
    )

    away_xg_per_shot = _safe_ratio(
        away_xg,
        away_total_shots,
    )

    home_in_box_ratio = _safe_ratio(
        home_in_box,
        home_total_shots,
    )

    away_in_box_ratio = _safe_ratio(
        away_in_box,
        away_total_shots,
    )

    home_outside_box_ratio = _safe_ratio(
        home_outside_box,
        home_total_shots,
    )

    away_outside_box_ratio = _safe_ratio(
        away_outside_box,
        away_total_shots,
    )

    home_big_conversion = _safe_ratio(
        home_big_scored,
        home_big_created,
    )

    away_big_conversion = _safe_ratio(
        away_big_scored,
        away_big_created,
    )

    home_shots_per_possession = _safe_ratio(
        home_total_shots,
        home_possession,
    )

    away_shots_per_possession = _safe_ratio(
        away_total_shots,
        away_possession,
    )

    home_xg_per_possession = _safe_ratio(
        home_xg,
        home_possession,
    )

    away_xg_per_possession = _safe_ratio(
        away_xg,
        away_possession,
    )

    # =====================================================
    # FEATURE COUNT
    # =====================================================

    # Sadece FeatureSet içindeki hesaplanabilir
    # feature değerlerini sayıyoruz.
    values = [
        home_goals,
        away_goals,
        home_xg,
        away_xg,
        xg_differential := _safe_difference(
            home_xg,
            away_xg,
        ),
        home_total_shots,
        away_total_shots,
        home_sot,
        away_sot,
        home_in_box,
        away_in_box,
        home_outside_box,
        away_outside_box,
        home_shot_accuracy,
        away_shot_accuracy,
        home_xg_per_shot,
        away_xg_per_shot,
        home_in_box_ratio,
        away_in_box_ratio,
        home_outside_box_ratio,
        away_outside_box_ratio,
        shot_differential := _safe_difference(
            home_total_shots,
            away_total_shots,
        ),
        sot_differential := _safe_difference(
            home_sot,
            away_sot,
        ),
        home_possession,
        away_possession,
        possession_differential := _safe_difference(
            home_possession,
            away_possession,
        ),
        home_shots_per_possession,
        away_shots_per_possession,
        home_xg_per_possession,
        away_xg_per_possession,
        home_corners,
        away_corners,
        corner_differential := _safe_difference(
            home_corners,
            away_corners,
        ),
        total_corners := (
            home_corners + away_corners
            if (
                home_corners is not None
                and away_corners is not None
            )
            else None
        ),
        home_big_created,
        away_big_created,
        home_big_scored,
        away_big_scored,
        home_big_missed,
        away_big_missed,
        home_big_conversion,
        away_big_conversion,
        home_passes,
        away_passes,
        home_touches,
        away_touches,
    ]

    available = sum(
        value is not None
        for value in values
    )

    missing = len(values) - available

    return FeatureSet(
        feature_engine_version=(
            FEATURE_ENGINE_VERSION
        ),
        home_goals=home_goals,
        away_goals=away_goals,
        home_xg=home_xg,
        away_xg=away_xg,
        xg_differential=xg_differential,
        home_total_shots=home_total_shots,
        away_total_shots=away_total_shots,
        home_shots_on_target=home_sot,
        away_shots_on_target=away_sot,
        home_shots_in_box=home_in_box,
        away_shots_in_box=away_in_box,
        home_shots_outside_box=home_outside_box,
        away_shots_outside_box=away_outside_box,
        home_shot_accuracy=home_shot_accuracy,
        away_shot_accuracy=away_shot_accuracy,
        home_xg_per_shot=home_xg_per_shot,
        away_xg_per_shot=away_xg_per_shot,
        home_shots_in_box_ratio=home_in_box_ratio,
        away_shots_in_box_ratio=away_in_box_ratio,
        home_shots_outside_box_ratio=home_outside_box_ratio,
        away_shots_outside_box_ratio=away_outside_box_ratio,
        shot_differential=shot_differential,
        shots_on_target_differential=sot_differential,
        home_possession=home_possession,
        away_possession=away_possession,
        possession_differential=possession_differential,
        home_shots_per_possession_point=(
            home_shots_per_possession
        ),
        away_shots_per_possession_point=(
            away_shots_per_possession
        ),
        home_xg_per_possession_point=(
            home_xg_per_possession
        ),
        away_xg_per_possession_point=(
            away_xg_per_possession
        ),
        home_corners=home_corners,
        away_corners=away_corners,
        corner_differential=corner_differential,
        total_corners=total_corners,
        home_big_chance_created=home_big_created,
        away_big_chance_created=away_big_created,
        home_big_chance_scored=home_big_scored,
        away_big_chance_scored=away_big_scored,
        home_big_chance_missed=home_big_missed,
        away_big_chance_missed=away_big_missed,
        home_big_chance_conversion=(
            home_big_conversion
        ),
        away_big_chance_conversion=(
            away_big_conversion
        ),
        home_passes=home_passes,
        away_passes=away_passes,
        home_touches_in_opp_box=home_touches,
        away_touches_in_opp_box=away_touches,
        available_feature_count=available,
        missing_feature_count=missing,
    )


def feature_set_to_dict(
    features: FeatureSet,
) -> dict[str, Any]:
    """FeatureSet'i dictionary olarak dışarı verir."""

    if not isinstance(
        features,
        FeatureSet,
    ):
        raise TypeError(
            "features FeatureSet olmalıdır."
        )

    return features.to_dict()
