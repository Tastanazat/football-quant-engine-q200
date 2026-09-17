"""
Q200 Engine - Feature Quality

Q200 V3.1

Feature Engine tarafından oluşturulan istatistiklerin:

- veri bulunabilirliğini,
- eksikliği,
- varyansını,
- birbirleriyle korelasyonunu,
- yüksek korelasyon nedeniyle oluşabilecek
  redundancy durumlarını

inceleyen salt-okunur kalite katmanıdır.

ÖNEMLİ:

Bu modül:
- lambda değiştirmez.
- model değiştirmez.
- odds kullanmaz.
- selection değiştirmez.
- stake değiştirmez.
- feature silmez.

Sadece kalite ve redundancy raporu üretir.

Nihai model feature seçimi daha sonra
ayrı bir aşamada yapılacaktır.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence


FEATURE_QUALITY_VERSION = (
    "Q200-FEATURE-QUALITY-V1"
)


DEFAULT_CORRELATION_THRESHOLD = 0.85


# =========================================================
# DATA STRUCTURES
# =========================================================

@dataclass(frozen=True)
class FeaturePair:
    """
    İki feature arasındaki korelasyon.
    """

    feature_a: str
    feature_b: str
    correlation: float
    absolute_correlation: float
    redundant: bool


@dataclass(frozen=True)
class FeatureQuality:
    """
    Tek feature için kalite özeti.
    """

    feature_name: str
    observation_count: int
    valid_count: int
    missing_count: int
    completeness: float
    mean: float | None
    minimum: float | None
    maximum: float | None
    variance: float | None
    constant: bool


@dataclass(frozen=True)
class FeatureQualityReport:
    """
    Tüm feature kalite değerlendirmesi.
    """

    version: str
    observation_count: int
    feature_count: int
    features: dict[str, FeatureQuality]
    correlations: list[FeaturePair]
    redundant_pairs: list[FeaturePair]
    threshold: float

    @property
    def redundant_feature_count(self) -> int:
        names: set[str] = set()

        for pair in self.redundant_pairs:
            names.add(pair.feature_a)
            names.add(pair.feature_b)

        return len(names)

    @property
    def usable_feature_count(self) -> int:
        return sum(
            quality.valid_count > 0
            and not quality.constant
            for quality in self.features.values()
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =========================================================
# VALIDATION
# =========================================================

def _validate_threshold(
    threshold: float,
) -> float:

    if isinstance(threshold, bool):
        raise TypeError(
            "threshold boolean olamaz."
        )

    try:
        value = float(threshold)

    except (TypeError, ValueError) as exc:

        raise TypeError(
            "threshold sayısal olmalıdır."
        ) from exc

    if not math.isfinite(value):

        raise ValueError(
            "threshold finite olmalıdır."
        )

    if not 0.0 <= value <= 1.0:

        raise ValueError(
            "threshold 0 ile 1 arasında olmalıdır."
        )

    return value


def _to_number(
    value: Any,
) -> float | None:

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        number = float(value)

    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _normalize_observations(
    observations: Iterable[
        Mapping[str, Any]
    ],
) -> list[dict[str, Any]]:

    if isinstance(
        observations,
        Mapping,
    ):
        raise TypeError(
            "observations mapping değil, "
            "mapping listesi olmalıdır."
        )

    normalized: list[
        dict[str, Any]
    ] = []

    for observation in observations:

        if not isinstance(
            observation,
            Mapping,
        ):
            raise TypeError(
                "Her observation mapping olmalıdır."
            )

        row: dict[str, Any] = {}

        for key, value in observation.items():

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "Feature isimleri string olmalıdır."
                )

            name = key.strip()

            if not name:
                raise ValueError(
                    "Boş feature adı kullanılamaz."
                )

            row[name] = value

        normalized.append(row)

    return normalized


# =========================================================
# BASIC STATISTICS
# =========================================================

def _mean(
    values: Sequence[float],
) -> float | None:

    if not values:
        return None

    return sum(values) / len(values)


def _variance(
    values: Sequence[float],
) -> float | None:

    if len(values) < 2:
        return None

    mean = sum(values) / len(values)

    return sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)


def _pearson(
    x: Sequence[float],
    y: Sequence[float],
) -> float | None:

    if len(x) != len(y):
        raise ValueError(
            "Pearson dizilerinin uzunlukları eşit olmalıdır."
        )

    if len(x) < 2:
        return None

    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    numerator = sum(
        (
            x_value - mean_x
        )
        * (
            y_value - mean_y
        )
        for x_value, y_value in zip(
            x,
            y,
        )
    )

    denominator_x = math.sqrt(
        sum(
            (
                value - mean_x
            ) ** 2
            for value in x
        )
    )

    denominator_y = math.sqrt(
        sum(
            (
                value - mean_y
            ) ** 2
            for value in y
        )
    )

    denominator = (
        denominator_x
        * denominator_y
    )

    if denominator == 0:
        return None

    correlation = (
        numerator
        / denominator
    )

    return max(
        -1.0,
        min(
            1.0,
            correlation,
        ),
    )


# =========================================================
# FEATURE DISCOVERY
# =========================================================

def discover_features(
    observations: Iterable[
        Mapping[str, Any]
    ],
) -> list[str]:
    """
    Dataset içerisindeki bütün feature isimlerini
    deterministik sırada döndürür.
    """

    normalized = _normalize_observations(
        observations
    )

    names: set[str] = set()

    for observation in normalized:
        names.update(
            observation.keys()
        )

    return sorted(names)


# =========================================================
# FEATURE QUALITY
# =========================================================

def assess_feature_quality(
    observations: Iterable[
        Mapping[str, Any]
    ],
) -> dict[str, FeatureQuality]:
    """
    Her feature için veri kalitesi hesaplar.
    """

    normalized = _normalize_observations(
        observations
    )

    feature_names = discover_features(
        normalized
    )

    total = len(normalized)

    result: dict[
        str,
        FeatureQuality,
    ] = {}

    for feature_name in feature_names:

        values: list[float] = []

        for observation in normalized:

            value = _to_number(
                observation.get(
                    feature_name
                )
            )

            if value is not None:
                values.append(value)

        valid_count = len(values)
        missing_count = (
            total
            - valid_count
        )

        completeness = (
            valid_count / total
            if total > 0
            else 0.0
        )

        mean = _mean(values)
        minimum = (
            min(values)
            if values
            else None
        )
        maximum = (
            max(values)
            if values
            else None
        )

        variance = _variance(
            values
        )

        constant = (
            valid_count >= 2
            and variance is not None
            and math.isclose(
                variance,
                0.0,
                abs_tol=1e-12,
            )
        )

        result[feature_name] = (
            FeatureQuality(
                feature_name=feature_name,
                observation_count=total,
                valid_count=valid_count,
                missing_count=missing_count,
                completeness=completeness,
                mean=mean,
                minimum=minimum,
                maximum=maximum,
                variance=variance,
                constant=constant,
            )
        )

    return result


# =========================================================
# CORRELATION
# =========================================================

def calculate_feature_correlation(
    observations: Iterable[
        Mapping[str, Any]
    ],
    feature_a: str,
    feature_b: str,
) -> float | None:
    """
    İki feature arasında Pearson korelasyonu hesaplar.

    Eksik değer bulunan satırlar sadece o çift için
    pairwise olarak dışarıda bırakılır.
    """

    normalized = _normalize_observations(
        observations
    )

    if not isinstance(
        feature_a,
        str,
    ):
        raise TypeError(
            "feature_a string olmalıdır."
        )

    if not isinstance(
        feature_b,
        str,
    ):
        raise TypeError(
            "feature_b string olmalıdır."
        )

    feature_a = feature_a.strip()
    feature_b = feature_b.strip()

    if not feature_a or not feature_b:
        raise ValueError(
            "Feature isimleri boş olamaz."
        )

    x: list[float] = []
    y: list[float] = []

    for observation in normalized:

        x_value = _to_number(
            observation.get(
                feature_a
            )
        )

        y_value = _to_number(
            observation.get(
                feature_b
            )
        )

        if (
            x_value is None
            or y_value is None
        ):
            continue

        x.append(x_value)
        y.append(y_value)

    return _pearson(
        x,
        y,
    )


def calculate_all_correlations(
    observations: Iterable[
        Mapping[str, Any]
    ],
) -> list[FeaturePair]:
    """
    Bütün feature çiftlerinin korelasyonunu hesaplar.

    Her çift yalnızca bir kez hesaplanır.
    """

    normalized = _normalize_observations(
        observations
    )

    feature_names = discover_features(
        normalized
    )

    result: list[
        FeaturePair
    ] = []

    for index, feature_a in enumerate(
        feature_names
    ):

        for feature_b in feature_names[
            index + 1:
        ]:

            correlation = (
                calculate_feature_correlation(
                    normalized,
                    feature_a,
                    feature_b,
                )
            )

            if correlation is None:
                continue

            result.append(
                FeaturePair(
                    feature_a=feature_a,
                    feature_b=feature_b,
                    correlation=correlation,
                    absolute_correlation=abs(
                        correlation
                    ),
                    redundant=False,
                )
            )

    return result


# =========================================================
# REDUNDANCY
# =========================================================

def find_redundant_features(
    observations: Iterable[
        Mapping[str, Any]
    ],
    *,
    threshold: float = (
        DEFAULT_CORRELATION_THRESHOLD
    ),
) -> list[FeaturePair]:
    """
    Korelasyonu threshold değerinin üzerinde olan
    feature çiftlerini bulur.

    Bu fonksiyon feature silmez.
    Sadece aday redundancy çiftlerini bildirir.
    """

    threshold = _validate_threshold(
        threshold
    )

    correlations = (
        calculate_all_correlations(
            observations
        )
    )

    result: list[
        FeaturePair
    ] = []

    for pair in correlations:

        if (
            pair.absolute_correlation
            >= threshold
        ):

            result.append(
                FeaturePair(
                    feature_a=pair.feature_a,
                    feature_b=pair.feature_b,
                    correlation=pair.correlation,
                    absolute_correlation=(
                        pair.absolute_correlation
                    ),
                    redundant=True,
                )
            )

    result.sort(
        key=lambda pair: (
            -pair.absolute_correlation,
            pair.feature_a,
            pair.feature_b,
        )
    )

    return result


# =========================================================
# COMPLETE REPORT
# =========================================================

def build_feature_quality_report(
    observations: Iterable[
        Mapping[str, Any]
    ],
    *,
    threshold: float = (
        DEFAULT_CORRELATION_THRESHOLD
    ),
) -> FeatureQualityReport:
    """
    Tam Feature Quality raporu üretir.
    """

    threshold = _validate_threshold(
        threshold
    )

    normalized = _normalize_observations(
        observations
    )

    qualities = (
        assess_feature_quality(
            normalized
        )
    )

    correlations = (
        calculate_all_correlations(
            normalized
        )
    )

    redundant = (
        find_redundant_features(
            normalized,
            threshold=threshold,
        )
    )

    return FeatureQualityReport(
        version=FEATURE_QUALITY_VERSION,
        observation_count=len(
            normalized
        ),
        feature_count=len(
            qualities
        ),
        features=qualities,
        correlations=correlations,
        redundant_pairs=redundant,
        threshold=threshold,
    )


def feature_quality_to_dict(
    report: FeatureQualityReport,
) -> dict[str, Any]:
    """
    Quality report'u dictionary'ye çevirir.
    """

    if not isinstance(
        report,
        FeatureQualityReport,
    ):
        raise TypeError(
            "report FeatureQualityReport olmalıdır."
        )

    return report.to_dict()
