"""
Q200 Engine - Feature Selection

Q200 V3.1

Feature Engine
      ↓
Feature Quality
      ↓
Feature Selection
      ↓
MODEL'E GİRECEK FEATURELER

Bu katman feature'ları sessizce silmez. Feature Quality raporunu
kullanarak her feature için KEEP / REVIEW / EXCLUDE kararını ve
kararın gerekçelerini üretir.

ÖNEMLİ:
- Model hesabı yapmaz.
- Lambda hesaplamaz.
- Odds kullanmaz.
- Kelly / stake hesabı yapmaz.
- Mevcut Q200 V3.1 modelini değiştirmez.
- Feature Quality katmanındaki veriyi değiştirmez.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .feature_quality import (
    DEFAULT_CORRELATION_THRESHOLD,
    FeaturePair,
    FeatureQuality,
    FeatureQualityReport,
)


FEATURE_SELECTION_VERSION = "Q200-FEATURE-SELECTION-V1"

# Mevcut public API ile uyumluluk.
DEFAULT_MAX_MISSING_RATE = 0.50
DEFAULT_REDUNDANCY_CORRELATION = DEFAULT_CORRELATION_THRESHOLD

# Yeni isim.
DEFAULT_MISSINGNESS_THRESHOLD = DEFAULT_MAX_MISSING_RATE

DECISIONS = ("KEEP", "REVIEW", "EXCLUDE")


@dataclass(frozen=True)
class FeatureSelectionDecision:
    """Tek feature için seçim kararı."""

    feature_name: str
    action: str
    reasons: tuple[str, ...] = ()
    completeness: float = 0.0
    missing_count: int = 0
    observation_count: int = 0
    constant: bool = False


@dataclass(frozen=True)
class FeatureSelectionReport:
    """Feature selection sonucu."""

    version: str
    observation_count: int
    feature_count: int
    selected_features: tuple[str, ...]
    review_features: tuple[str, ...]
    excluded_features: tuple[str, ...]
    decisions: tuple[FeatureSelectionDecision, ...]
    redundant_pairs: tuple[tuple[str, str], ...]
    missingness_threshold: float
    correlation_threshold: float

    @property
    def selected_feature_count(self) -> int:
        return len(self.selected_features)

    @property
    def review_feature_count(self) -> int:
        return len(self.review_features)

    @property
    def excluded_feature_count(self) -> int:
        return len(self.excluded_features)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_threshold(
    value: float,
    *,
    name: str,
) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} sayı olmalıdır.")

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} sayı olmalıdır.") from exc

    if numeric != numeric:
        raise ValueError(f"{name} finite olmalıdır.")

    if numeric in (float("inf"), float("-inf")):
        raise ValueError(f"{name} finite olmalıdır.")

    if not 0.0 <= numeric <= 1.0:
        raise ValueError(
            f"{name} 0 ile 1 arasında olmalıdır."
        )

    return numeric


def _validate_quality_report(
    report: FeatureQualityReport,
) -> FeatureQualityReport:
    if not isinstance(report, FeatureQualityReport):
        raise TypeError(
            "report FeatureQualityReport olmalıdır."
        )

    return report


def _quality_reason(
    quality: FeatureQuality,
    *,
    missingness_threshold: float,
) -> list[str]:

    reasons: list[str] = []

    if quality.observation_count <= 0:
        reasons.append("NO_OBSERVATIONS")
        return reasons

    if quality.valid_count <= 0:
        reasons.append("NO_VALID_VALUES")

    missing_rate = (
        quality.missing_count / quality.observation_count
        if quality.observation_count > 0
        else 1.0
    )

    if missing_rate > missingness_threshold:
        reasons.append("HIGH_MISSINGNESS")

    if quality.constant:
        reasons.append("CONSTANT_FEATURE")

    return reasons


def _redundant_feature_names(
    redundant_pairs: Iterable[FeaturePair],
) -> set[str]:

    names: set[str] = set()

    for pair in redundant_pairs:

        if isinstance(pair.feature_a, str):
            names.add(pair.feature_a)

        if isinstance(pair.feature_b, str):
            names.add(pair.feature_b)

    return names


def _build_report(
    report: FeatureQualityReport,
    *,
    missingness_threshold: float,
    correlation_threshold: float,
) -> FeatureSelectionReport:

    redundant_pairs = tuple(
        report.redundant_pairs
    )

    redundant_names = _redundant_feature_names(
        redundant_pairs
    )

    decisions: list[
        FeatureSelectionDecision
    ] = []

    # FeatureQualityReport.features:
    # dict[str, FeatureQuality]
    #
    # sorted() kullanımı çıktının deterministik
    # olmasını sağlar.

    for feature_name in sorted(report.features):

        quality = report.features[feature_name]

        reasons = _quality_reason(
            quality,
            missingness_threshold=missingness_threshold,
        )

        if feature_name in redundant_names:
            reasons.append(
                "HIGH_CORRELATION"
            )

        # Aynı sebebin iki kez eklenmesini engeller.
        reasons = list(
            dict.fromkeys(reasons)
        )

        action = (
            "REVIEW"
            if reasons
            else "KEEP"
        )

        decisions.append(
            FeatureSelectionDecision(
                feature_name=feature_name,
                action=action,
                reasons=tuple(reasons),
                completeness=quality.completeness,
                missing_count=quality.missing_count,
                observation_count=quality.observation_count,
                constant=quality.constant,
            )
        )

    selected_features = tuple(
        item.feature_name
        for item in decisions
        if item.action == "KEEP"
    )

    review_features = tuple(
        item.feature_name
        for item in decisions
        if item.action == "REVIEW"
    )

    excluded_features = tuple(
        item.feature_name
        for item in decisions
        if item.action == "EXCLUDE"
    )

    return FeatureSelectionReport(
        version=FEATURE_SELECTION_VERSION,
        observation_count=report.observation_count,
        feature_count=report.feature_count,
        selected_features=selected_features,
        review_features=review_features,
        excluded_features=excluded_features,
        decisions=tuple(decisions),
        redundant_pairs=tuple(
            (
                pair.feature_a,
                pair.feature_b,
            )
            for pair in redundant_pairs
        ),
        missingness_threshold=missingness_threshold,
        correlation_threshold=correlation_threshold,
    )


def build_feature_selection(
    report: FeatureQualityReport,
    *,
    missingness_threshold: float = DEFAULT_MISSINGNESS_THRESHOLD,
    correlation_threshold: float = DEFAULT_CORRELATION_THRESHOLD,
) -> FeatureSelectionReport:
    """
    Feature Quality raporundan Feature Selection raporu üretir.

    Kurallar:

    1. Gözlemi olmayan feature REVIEW.
    2. Geçerli değeri olmayan feature REVIEW.
    3. Missingness threshold aşılırsa REVIEW.
    4. Constant feature REVIEW.
    5. Redundant/high-correlation feature REVIEW.
    6. Problem olmayan feature KEEP.

    Otomatik EXCLUDE yapılmaz.
    """

    report = _validate_quality_report(
        report
    )

    missingness_threshold = _validate_threshold(
        missingness_threshold,
        name="missingness_threshold",
    )

    correlation_threshold = _validate_threshold(
        correlation_threshold,
        name="correlation_threshold",
    )

    return _build_report(
        report,
        missingness_threshold=missingness_threshold,
        correlation_threshold=correlation_threshold,
    )


def select_features(
    report: FeatureQualityReport,
    *,
    max_missing_rate: float = DEFAULT_MAX_MISSING_RATE,
    redundancy_correlation: float = DEFAULT_REDUNDANCY_CORRELATION,
) -> FeatureSelectionReport:
    """
    Mevcut public API ile feature selection çalıştırır.
    """

    return build_feature_selection(
        report,
        missingness_threshold=max_missing_rate,
        correlation_threshold=redundancy_correlation,
    )


def discover_selection_candidates(
    report: FeatureQualityReport,
    *,
    max_missing_rate: float = DEFAULT_MAX_MISSING_RATE,
    redundancy_correlation: float = DEFAULT_REDUNDANCY_CORRELATION,
) -> tuple[str, ...]:
    """
    REVIEW edilmesi gereken feature adaylarını döndürür.
    """

    selection = select_features(
        report,
        max_missing_rate=max_missing_rate,
        redundancy_correlation=redundancy_correlation,
    )

    return selection.review_features


def selected_feature_names(
    selection: FeatureSelectionReport,
) -> tuple[str, ...]:

    if not isinstance(
        selection,
        FeatureSelectionReport,
    ):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return selection.selected_features


def review_feature_names(
    selection: FeatureSelectionReport,
) -> tuple[str, ...]:

    if not isinstance(
        selection,
        FeatureSelectionReport,
    ):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return selection.review_features


def feature_selection_to_dict(
    selection: FeatureSelectionReport,
) -> dict[str, Any]:

    if not isinstance(
        selection,
        FeatureSelectionReport,
    ):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return selection.to_dict()


def feature_selection_summary(
    selection: FeatureSelectionReport,
) -> dict[str, Any]:
    """
    Kısa JSON uyumlu selection özeti.
    """

    if not isinstance(
        selection,
        FeatureSelectionReport,
    ):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return {
        "version": selection.version,
        "observation_count": (
            selection.observation_count
        ),
        "feature_count": (
            selection.feature_count
        ),
        "selected_feature_count": len(
            selection.selected_features
        ),
        "review_feature_count": len(
            selection.review_features
        ),
        "excluded_feature_count": len(
            selection.excluded_features
        ),
        "selected_features": (
            selection.selected_features
        ),
        "review_features": (
            selection.review_features
        ),
        "excluded_features": (
            selection.excluded_features
        ),
    }


def filter_feature_mapping(
    values: Mapping[str, Any],
    selection: FeatureSelectionReport,
    *,
    include_review: bool = False,
) -> dict[str, Any]:
    """
    Feature mapping'i selection sonucuna göre filtreler.

    Varsayılan:
        yalnızca KEEP feature'ları döndürür.

    include_review=True:
        KEEP + REVIEW döndürür.

    EXCLUDE hiçbir durumda döndürülmez.
    """

    if not isinstance(
        values,
        Mapping,
    ):
        raise TypeError(
            "values mapping olmalıdır."
        )

    if not isinstance(
        selection,
        FeatureSelectionReport,
    ):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    allowed = set(
        selection.selected_features
    )

    if include_review:
        allowed.update(
            selection.review_features
        )

    return {
        key: value
        for key, value in values.items()
        if key in allowed
    }


__all__ = [
    "FEATURE_SELECTION_VERSION",
    "DEFAULT_MAX_MISSING_RATE",
    "DEFAULT_REDUNDANCY_CORRELATION",
    "DEFAULT_MISSINGNESS_THRESHOLD",
    "DECISIONS",
    "FeatureSelectionDecision",
    "FeatureSelectionReport",
    "discover_selection_candidates",
    "select_features",
    "build_feature_selection",
    "selected_feature_names",
    "review_feature_names",
    "feature_selection_to_dict",
    "feature_selection_summary",
    "filter_feature_mapping",
]
