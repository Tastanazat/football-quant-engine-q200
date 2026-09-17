"""
Q200 Engine - Feature Selection

Q200 V3.1

Feature Quality çıktısını kullanarak model öncesi feature
seçim/inceleme raporu oluşturur.

Bu katman:
- Model hesabı yapmaz.
- Lambda hesabı yapmaz.
- Odds kullanmaz.
- Selection/stake değiştirmez.
- Feature silmez.
- Yalnızca feature'ları kalite kriterlerine göre sınıflandırır.
- Her sınıflandırma için neden üretir.

Karar seviyeleri:

KEEP
    Feature mevcut durumda kullanılabilir görünüyor.

FLAG
    Feature kullanılabilir olabilir ancak veri kalitesi nedeniyle
    ayrıca incelenmelidir.

REDUNDANT
    Feature başka bir feature ile yüksek korelasyon gösteriyor.
    Otomatik olarak silinmez.

EXCLUDE
    Feature mevcut haliyle model adayı olmamalıdır.

ÖNEMLİ:
Bu rapor yalnızca karar desteğidir. Q200 modelinin hangi
feature'ları kullanacağına henüz müdahale etmez.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence


FEATURE_SELECTION_VERSION = "Q200-FEATURE-SELECTION-V1"

DEFAULT_MAX_MISSING_RATE = 0.50
DEFAULT_REDUNDANCY_CORRELATION = 0.85


DECISIONS = frozenset(
    {
        "KEEP",
        "FLAG",
        "REDUNDANT",
        "EXCLUDE",
    }
)


@dataclass(frozen=True)
class FeatureSelectionDecision:
    """
    Tek bir feature için seçim kararı.
    """

    feature_name: str
    decision: str
    reasons: tuple[str, ...]
    completeness: float
    missing_rate: float
    observation_count: int
    valid_count: int
    constant: bool


@dataclass(frozen=True)
class FeatureSelectionReport:
    """
    Feature Selection raporu.

    Bu nesne salt-okunurdur ve model davranışını değiştirmez.
    """

    version: str
    observation_count: int
    feature_count: int
    max_missing_rate: float
    redundancy_correlation: float
    decisions: tuple[FeatureSelectionDecision, ...]
    redundant_pairs: tuple[tuple[str, str], ...]


def _validate_threshold(
    value: float,
    *,
    name: str,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} sayısal olmalıdır.")

    value = float(value)

    if value < minimum or value > maximum:
        raise ValueError(
            f"{name} {minimum} ile {maximum} arasında olmalıdır."
        )

    return value


def _validate_non_negative_int(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} integer olmalıdır.")

    if value < 0:
        raise ValueError(f"{name} negatif olamaz.")

    return value


def _read_quality_value(
    quality: Any,
    name: str,
    default: Any = None,
) -> Any:
    """
    Dataclass veya mapping tabanlı FeatureQuality nesnelerini destekler.
    """

    if isinstance(quality, Mapping):
        return quality.get(name, default)

    return getattr(quality, name, default)


def _missing_rate(quality: Any) -> float:
    completeness = _read_quality_value(quality, "completeness")

    if completeness is not None:
        completeness = float(completeness)
        return max(0.0, min(1.0, 1.0 - completeness))

    observation_count = _read_quality_value(
        quality,
        "observation_count",
        0,
    )

    missing_count = _read_quality_value(
        quality,
        "missing_count",
        0,
    )

    observation_count = _validate_non_negative_int(
        int(observation_count),
        name="observation_count",
    )

    missing_count = _validate_non_negative_int(
        int(missing_count),
        name="missing_count",
    )

    if observation_count == 0:
        return 1.0

    return min(
        1.0,
        max(0.0, missing_count / observation_count),
    )


def _feature_name(quality: Any) -> str:
    name = _read_quality_value(quality, "feature_name")

    if name is None:
        name = _read_quality_value(quality, "name")

    if name is None:
        raise ValueError("Feature kalite kaydında feature_name bulunamadı.")

    name = str(name).strip()

    if not name:
        raise ValueError("Feature adı boş olamaz.")

    return name


def _observation_count(quality: Any) -> int:
    value = _read_quality_value(
        quality,
        "observation_count",
        0,
    )

    return _validate_non_negative_int(
        int(value),
        name="observation_count",
    )


def _valid_count(quality: Any) -> int:
    value = _read_quality_value(
        quality,
        "valid_count",
        0,
    )

    return _validate_non_negative_int(
        int(value),
        name="valid_count",
    )


def _constant(quality: Any) -> bool:
    return bool(
        _read_quality_value(
            quality,
            "constant",
            False,
        )
    )


def _validate_decision(decision: str) -> str:
    decision = str(decision).upper().strip()

    if decision not in DECISIONS:
        raise ValueError(
            f"Geçersiz feature selection kararı: {decision}"
        )

    return decision


def discover_selection_candidates(
    quality_report: Any,
) -> list[Any]:
    """
    FeatureQualityReport içindeki feature kalite kayıtlarını alır.

    Hem dataclass hem mapping tabanlı raporları destekler.
    """

    if isinstance(quality_report, Mapping):
        features = quality_report.get("features", ())
    else:
        features = getattr(quality_report, "features", ())

    if features is None:
        return []

    return list(features)


def select_features(
    quality_report: Any,
    *,
    max_missing_rate: float = DEFAULT_MAX_MISSING_RATE,
    redundancy_correlation: float = DEFAULT_REDUNDANCY_CORRELATION,
) -> FeatureSelectionReport:
    """
    Feature Quality raporundan Feature Selection raporu üretir.

    Hiçbir feature fiziksel olarak silinmez.

    Karar mantığı:

    1. Çok yüksek eksiklik:
       EXCLUDE

    2. Constant feature:
       FLAG

    3. Orta/yüksek eksiklik:
       FLAG

    4. Diğerleri:
       KEEP

    Korelasyon nedeniyle REDUNDANT kararı ayrıca
    redundant_pairs üzerinden raporlanır.
    """

    max_missing_rate = _validate_threshold(
        max_missing_rate,
        name="max_missing_rate",
    )

    redundancy_correlation = _validate_threshold(
        redundancy_correlation,
        name="redundancy_correlation",
    )

    candidates = discover_selection_candidates(quality_report)

    observation_count = _read_quality_value(
        quality_report,
        "observation_count",
        0,
    )

    observation_count = _validate_non_negative_int(
        int(observation_count),
        name="observation_count",
    )

    decisions: list[FeatureSelectionDecision] = []

    for quality in candidates:
        name = _feature_name(quality)

        observations = _observation_count(quality)
        valid = _valid_count(quality)
        constant = _constant(quality)
        missing_rate = _missing_rate(quality)
        completeness = 1.0 - missing_rate

        reasons: list[str] = []

        if observations == 0:
            reasons.append("NO_OBSERVATIONS")

        if valid == 0:
            reasons.append("NO_VALID_VALUES")

        if missing_rate > max_missing_rate:
            reasons.append("HIGH_MISSING_RATE")

        elif missing_rate > 0:
            reasons.append("PARTIAL_MISSING_DATA")

        if constant:
            reasons.append("CONSTANT_FEATURE")

        if missing_rate > max_missing_rate or valid == 0:
            decision = "EXCLUDE"

        elif constant:
            decision = "FLAG"

        elif missing_rate > 0:
            decision = "FLAG"

        else:
            decision = "KEEP"

        if not reasons:
            reasons.append("DATA_QUALITY_ACCEPTABLE")

        decisions.append(
            FeatureSelectionDecision(
                feature_name=name,
                decision=_validate_decision(decision),
                reasons=tuple(reasons),
                completeness=completeness,
                missing_rate=missing_rate,
                observation_count=observations,
                valid_count=valid,
                constant=constant,
            )
        )

    decisions.sort(key=lambda item: item.feature_name)

    redundant_pairs = _extract_redundant_pairs(
        quality_report,
        threshold=redundancy_correlation,
    )

    redundant_names = {
        name
        for pair in redundant_pairs
        for name in pair
    }

    updated_decisions: list[FeatureSelectionDecision] = []

    for decision in decisions:
        if (
            decision.feature_name in redundant_names
            and decision.decision == "KEEP"
        ):
            reasons = tuple(
                list(decision.reasons)
                + ["HIGH_CORRELATION_REDUNDANCY"]
            )

            updated_decisions.append(
                FeatureSelectionDecision(
                    feature_name=decision.feature_name,
                    decision="REDUNDANT",
                    reasons=reasons,
                    completeness=decision.completeness,
                    missing_rate=decision.missing_rate,
                    observation_count=decision.observation_count,
                    valid_count=decision.valid_count,
                    constant=decision.constant,
                )
            )
        elif (
            decision.feature_name in redundant_names
            and decision.decision == "FLAG"
        ):
            reasons = tuple(
                list(decision.reasons)
                + ["HIGH_CORRELATION_REDUNDANCY"]
            )

            updated_decisions.append(
                FeatureSelectionDecision(
                    feature_name=decision.feature_name,
                    decision="FLAG",
                    reasons=reasons,
                    completeness=decision.completeness,
                    missing_rate=decision.missing_rate,
                    observation_count=decision.observation_count,
                    valid_count=decision.valid_count,
                    constant=decision.constant,
                )
            )
        else:
            updated_decisions.append(decision)

    return FeatureSelectionReport(
        version=FEATURE_SELECTION_VERSION,
        observation_count=observation_count,
        feature_count=len(updated_decisions),
        max_missing_rate=max_missing_rate,
        redundancy_correlation=redundancy_correlation,
        decisions=tuple(updated_decisions),
        redundant_pairs=tuple(redundant_pairs),
    )


def _extract_redundant_pairs(
    quality_report: Any,
    *,
    threshold: float,
) -> list[tuple[str, str]]:
    """
    FeatureQualityReport içindeki correlation bilgilerini okur.

    Desteklenen yapılar:

    correlations:
        {
            ("a", "b"): 0.91,
            ...
        }

    veya:

    correlations:
        [
            FeaturePair(...),
            ...
        ]

    veya FeaturePair nesneleri.
    """

    if isinstance(quality_report, Mapping):
        correlations = quality_report.get("correlations", ())
        existing_pairs = quality_report.get("redundant_pairs", ())
    else:
        correlations = getattr(quality_report, "correlations", ())
        existing_pairs = getattr(
            quality_report,
            "redundant_pairs",
            (),
        )

    pairs: set[tuple[str, str]] = set()

    for item in existing_pairs or ():
        pair = _parse_pair(item)

        if pair is not None:
            pairs.add(pair)

    if isinstance(correlations, Mapping):
        for key, value in correlations.items():
            pair = _parse_pair_key(key)

            if pair is None:
                continue

            try:
                correlation = float(value)
            except (TypeError, ValueError):
                continue

            if abs(correlation) >= threshold:
                pairs.add(pair)

    else:
        for item in correlations or ():
            pair = _parse_pair(item)

            if pair is None:
                continue

            correlation = _read_quality_value(
                item,
                "absolute_correlation",
            )

            if correlation is None:
                correlation = _read_quality_value(
                    item,
                    "correlation",
                )

                try:
                    correlation = abs(float(correlation))
                except (TypeError, ValueError):
                    continue

            try:
                correlation = float(correlation)
            except (TypeError, ValueError):
                continue

            if correlation >= threshold:
                pairs.add(pair)

    return sorted(pairs)


def _parse_pair_key(key: Any) -> tuple[str, str] | None:
    if not isinstance(key, (tuple, list)):
        return None

    if len(key) != 2:
        return None

    first = str(key[0]).strip()
    second = str(key[1]).strip()

    if not first or not second or first == second:
        return None

    return tuple(sorted((first, second)))


def _parse_pair(item: Any) -> tuple[str, str] | None:
    if isinstance(item, (tuple, list)):
        return _parse_pair_key(item)

    feature_a = _read_quality_value(item, "feature_a")
    feature_b = _read_quality_value(item, "feature_b")

    if feature_a is None or feature_b is None:
        return None

    feature_a = str(feature_a).strip()
    feature_b = str(feature_b).strip()

    if (
        not feature_a
        or not feature_b
        or feature_a == feature_b
    ):
        return None

    return tuple(sorted((feature_a, feature_b)))


def selected_feature_names(
    report: FeatureSelectionReport,
    *,
    include_flagged: bool = False,
    include_redundant: bool = False,
) -> tuple[str, ...]:
    """
    Selection raporundan kullanılabilecek feature isimlerini döndürür.

    Varsayılan:
        yalnızca KEEP.

    Bu fonksiyon model.py'yi değiştirmez.
    """

    if not isinstance(report, FeatureSelectionReport):
        raise TypeError(
            "report FeatureSelectionReport olmalıdır."
        )

    allowed = {"KEEP"}

    if include_flagged:
        allowed.add("FLAG")

    if include_redundant:
        allowed.add("REDUNDANT")

    return tuple(
        decision.feature_name
        for decision in report.decisions
        if decision.decision in allowed
    )


def feature_selection_to_dict(
    report: FeatureSelectionReport,
) -> dict[str, Any]:
    """
    FeatureSelectionReport'u JSON uyumlu dict'e dönüştürür.
    """

    if not isinstance(report, FeatureSelectionReport):
        raise TypeError(
            "report FeatureSelectionReport olmalıdır."
        )

    return asdict(report)


def feature_selection_summary(
    report: FeatureSelectionReport,
) -> dict[str, int]:
    """
    Kararların özetini döndürür.
    """

    if not isinstance(report, FeatureSelectionReport):
        raise TypeError(
            "report FeatureSelectionReport olmalıdır."
        )

    summary = {
        "KEEP": 0,
        "FLAG": 0,
        "REDUNDANT": 0,
        "EXCLUDE": 0,
    }

    for decision in report.decisions:
        summary[decision.decision] += 1

    return summary


__all__ = [
    "FEATURE_SELECTION_VERSION",
    "DEFAULT_MAX_MISSING_RATE",
    "DEFAULT_REDUNDANCY_CORRELATION",
    "DECISIONS",
    "FeatureSelectionDecision",
    "FeatureSelectionReport",
    "discover_selection_candidates",
    "select_features",
    "selected_feature_names",
    "feature_selection_to_dict",
    "feature_selection_summary",
]
