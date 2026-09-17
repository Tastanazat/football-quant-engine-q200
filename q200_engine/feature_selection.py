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

Bu katman feature'ları otomatik olarak silmez.

Amaç:
- eksikliği yüksek feature'ları işaretlemek
- sabit feature'ları işaretlemek
- yüksek korelasyonlu feature çiftlerini işaretlemek
- seçim gerekçelerini kayıt altına almak
- model katmanına hangi feature'ların gönderileceğini
  açık ve denetlenebilir hale getirmek

ÖNEMLİ:
- Model hesabı yapmaz.
- Lambda hesaplamaz.
- Odds kullanmaz.
- Selection / Kelly hesabı yapmaz.
- Mevcut Q200 V3.1 modelini değiştirmez.
- Feature'ları sessizce silmez.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .feature_quality import (
    DEFAULT_CORRELATION_THRESHOLD,
    FeatureQualityReport,
)


FEATURE_SELECTION_VERSION = "Q200-FEATURE-SELECTION-V1"

DEFAULT_MISSINGNESS_THRESHOLD = 0.50


@dataclass(frozen=True)
class FeatureSelectionDecision:
    """
    Tek bir feature için seçim kararı.

    action:
        KEEP
        REVIEW
        EXCLUDE

    Q200 şu aşamada otomatik EXCLUDE uygulamaz.
    EXCLUDE yalnızca açıkça verilen manuel seçimlerde kullanılabilir.
    """

    feature_name: str
    action: str
    reasons: tuple[str, ...] = ()
    completeness: float = 0.0
    missing_count: int = 0
    observation_count: int = 0
    constant: bool = False


@dataclass(frozen=True)
class FeatureSelectionReport:
    """
    Feature selection raporu.

    Bu rapor model parametrelerini değiştirmez.
    Yalnızca feature seçiminin gerekçesini kayıt altına alır.
    """

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


def _validate_threshold(
    value: float,
    *,
    name: str,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Threshold değerini doğrular.
    """

    if isinstance(value, bool):
        raise TypeError(f"{name} sayı olmalıdır.")

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} sayı olmalıdır.") from exc

    if numeric < minimum or numeric > maximum:
        raise ValueError(
            f"{name} {minimum} ile {maximum} arasında olmalıdır."
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
    quality: Any,
    *,
    missingness_threshold: float,
) -> list[str]:
    """
    Feature Quality çıktısından seçim gerekçelerini üretir.
    """

    reasons: list[str] = []

    if quality.observation_count <= 0:
        reasons.append("NO_OBSERVATIONS")
        return reasons

    if quality.completeness < (1.0 - missingness_threshold):
        reasons.append("HIGH_MISSINGNESS")

    if quality.constant:
        reasons.append("CONSTANT_FEATURE")

    if quality.valid_count <= 0:
        reasons.append("NO_VALID_VALUES")

    return reasons


def _redundant_feature_names(
    redundant_pairs: Iterable[Any],
) -> set[str]:
    """
    Feature Quality redundant pair listesinden feature isimlerini çıkarır.
    """

    names: set[str] = set()

    for pair in redundant_pairs:
        feature_a = getattr(pair, "feature_a", None)
        feature_b = getattr(pair, "feature_b", None)

        if isinstance(feature_a, str):
            names.add(feature_a)

        if isinstance(feature_b, str):
            names.add(feature_b)

    return names


def build_feature_selection(
    report: FeatureQualityReport,
    *,
    missingness_threshold: float = DEFAULT_MISSINGNESS_THRESHOLD,
    correlation_threshold: float = DEFAULT_CORRELATION_THRESHOLD,
) -> FeatureSelectionReport:
    """
    Feature Quality raporundan Feature Selection raporu üretir.

    Kurallar:

    1. Feature'ın gözlemi yoksa REVIEW.
    2. Feature'ın geçerli değeri yoksa REVIEW.
    3. Missingness threshold aşılırsa REVIEW.
    4. Constant feature REVIEW.
    5. Yüksek korelasyonlu feature'lar REVIEW.
    6. Hiçbir problem yoksa KEEP.

    Otomatik EXCLUDE yapılmaz.
    """

    report = _validate_quality_report(report)

    missingness_threshold = _validate_threshold(
        missingness_threshold,
        name="missingness_threshold",
    )

    correlation_threshold = _validate_threshold(
        correlation_threshold,
        name="correlation_threshold",
    )

    redundant_pairs = tuple(report.redundant_pairs)

    redundant_names = _redundant_feature_names(
        redundant_pairs
    )

    decisions: list[FeatureSelectionDecision] = []

    for quality in report.features:
        reasons = _quality_reason(
            quality,
            missingness_threshold=missingness_threshold,
        )

        if quality.feature_name in redundant_names:
            reasons.append("HIGH_CORRELATION")

        # Duplicate reason koruması.
        reasons = list(dict.fromkeys(reasons))

        if reasons:
            action = "REVIEW"
        else:
            action = "KEEP"

        decisions.append(
            FeatureSelectionDecision(
                feature_name=quality.feature_name,
                action=action,
                reasons=tuple(reasons),
                completeness=quality.completeness,
                missing_count=quality.missing_count,
                observation_count=quality.observation_count,
                constant=quality.constant,
            )
        )

    selected_features = tuple(
        decision.feature_name
        for decision in decisions
        if decision.action == "KEEP"
    )

    review_features = tuple(
        decision.feature_name
        for decision in decisions
        if decision.action == "REVIEW"
    )

    excluded_features = tuple(
        decision.feature_name
        for decision in decisions
        if decision.action == "EXCLUDE"
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


def selected_feature_names(
    selection: FeatureSelectionReport,
) -> tuple[str, ...]:
    """
    KEEP olarak işaretlenen feature isimlerini döndürür.
    """

    if not isinstance(selection, FeatureSelectionReport):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return selection.selected_features


def review_feature_names(
    selection: FeatureSelectionReport,
) -> tuple[str, ...]:
    """
    REVIEW olarak işaretlenen feature isimlerini döndürür.
    """

    if not isinstance(selection, FeatureSelectionReport):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return selection.review_features


def feature_selection_to_dict(
    selection: FeatureSelectionReport,
) -> dict[str, Any]:
    """
    Selection raporunu JSON uyumlu dictionary'ye çevirir.
    """

    if not isinstance(selection, FeatureSelectionReport):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    return asdict(selection)


def filter_feature_mapping(
    values: Mapping[str, Any],
    selection: FeatureSelectionReport,
    *,
    include_review: bool = False,
) -> dict[str, Any]:
    """
    Feature mapping'i selection raporuna göre filtreler.

    Varsayılan:
        yalnızca KEEP feature'ları döndürür.

    include_review=True:
        KEEP + REVIEW feature'ları döndürür.

    EXCLUDE feature'ları hiçbir durumda döndürülmez.
    """

    if not isinstance(values, Mapping):
        raise TypeError(
            "values mapping olmalıdır."
        )

    if not isinstance(selection, FeatureSelectionReport):
        raise TypeError(
            "selection FeatureSelectionReport olmalıdır."
        )

    allowed = set(selection.selected_features)

    if include_review:
        allowed.update(selection.review_features)

    return {
        key: value
        for key, value in values.items()
        if key in allowed
    }


__all__ = [
    "FEATURE_SELECTION_VERSION",
    "DEFAULT_MISSINGNESS_THRESHOLD",
    "FeatureSelectionDecision",
    "FeatureSelectionReport",
    "build_feature_selection",
    "selected_feature_names",
    "review_feature_names",
    "feature_selection_to_dict",
    "filter_feature_mapping",
]
