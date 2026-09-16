"""
Q200 Engine - Calibration

Q200 V3.1

Kayıtlı analizlerdeki model olasılıklarını gerçekleşen sonuçlarla
karşılaştırır.

Bu katman:
- Model hesabını değiştirmez.
- Odds hesabını değiştirmez.
- Selection üretmez.
- Settlement verisini değiştirmez.
- Sadece gerçekleşmiş ve settlement edilmiş seçimlerden ölçüm üretir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


CALIBRATION_VERSION = "Q200-CALIBRATION-V1"


@dataclass(frozen=True)
class CalibrationSummary:
    """Genel calibration performans özeti."""

    total_predictions: int
    evaluated_predictions: int
    void_predictions: int
    missing_probability_predictions: int

    brier_score: float
    log_loss: float

    mean_predicted_probability: float
    empirical_win_rate: float

    @property
    def coverage(self) -> float:
        """Değerlendirilebilen tahminlerin toplam içindeki oranı."""

        if self.total_predictions <= 0:
            return 0.0

        return (
            self.evaluated_predictions
            / self.total_predictions
        )


@dataclass(frozen=True)
class CalibrationBucket:
    """Tek bir probability calibration bucket'ı."""

    lower_bound: float
    upper_bound: float

    predictions: int
    wins: int

    mean_predicted_probability: float
    empirical_win_rate: float


@dataclass(frozen=True)
class CalibrationObservation:
    """Tek bir tahmin-gerçekleşme gözlemi."""

    market: str
    predicted_probability: float
    actual: int


def _probability(
    value: Any,
    name: str,
) -> float:

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            f"{name} sayısal olmalıdır."
        )

    try:

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            f"{name} sayısal olmalıdır."
        ) from exc

    if (
        not math.isfinite(
            result
        )
        or not 0.0 <= result <= 1.0
    ):

        raise ValueError(
            f"{name} 0 ile 1 arasında olmalıdır."
        )

    return result


def _validate_history(
    history: Any,
) -> None:

    if history is None:

        raise TypeError(
            "history verilmelidir."
        )

    required_methods = (
        "count",
        "list",
        "get",
    )

    for method in required_methods:

        if not callable(
            getattr(
                history,
                method,
                None,
            )
        ):

            raise TypeError(
                "history AnalysisHistory benzeri "
                "bir repository olmalıdır."
            )


def _prediction_probability(
    record: dict[str, Any],
    outcome: str,
) -> float | None:
    """
    Calibration için model olasılığını bulur.

    Öncelik:

    1. stress_test -> BASELINE
    2. model -> probabilities

    PESSIMISTIC probability kullanılmaz.

    Çünkü calibration modelin gerçek tahmin olasılığını ölçmelidir;
    stress senaryosu calibration verisini değiştirmemelidir.
    """

    report = record.get(
        "report"
    )

    if not isinstance(
        report,
        dict,
    ):

        raise ValueError(
            "History report dictionary olmalıdır."
        )

    stress_test = report.get(
        "stress_test"
    )

    if isinstance(
        stress_test,
        dict,
    ):

        probabilities = stress_test.get(
            "probabilities"
        )

        if isinstance(
            probabilities,
            dict,
        ):

            baseline = probabilities.get(
                "BASELINE"
            )

            if isinstance(
                baseline,
                dict,
            ) and outcome in baseline:

                return _probability(
                    baseline[outcome],
                    f"{outcome} baseline probability",
                )

    model = report.get(
        "model"
    )

    if isinstance(
        model,
        dict,
    ):

        probabilities = model.get(
            "probabilities"
        )

        if (
            isinstance(
                probabilities,
                dict,
            )
            and outcome in probabilities
        ):

            return _probability(
                probabilities[outcome],
                f"{outcome} model probability",
            )

    return None


def collect_observations(
    history,
) -> tuple[
    list[CalibrationObservation],
    int,
    int,
]:
    """
    Settlement edilmiş seçimlerden calibration gözlemleri çıkarır.

    WIN  -> actual = 1
    LOSS -> actual = 0
    VOID -> calibration dışında

    Probability önceliği:

    1. stress_test.probabilities.BASELINE
    2. model.probabilities
    """

    _validate_history(
        history
    )

    total = history.count()

    if total > 0:

        records = history.list(
            limit=total
        )

    else:

        records = []

    observations: list[
        CalibrationObservation
    ] = []

    void_predictions = 0
    missing_probability_predictions = 0

    for item in records:

        if item.get(
            "settlement_recorded"
        ) is not True:

            continue

        record = history.get(
            item["id"]
        )

        if record is None:

            continue

        settlement = record.get(
            "settlement"
        )

        if not isinstance(
            settlement,
            dict,
        ):

            raise ValueError(
                "Settlement dictionary olmalıdır."
            )

        selections = settlement.get(
            "selections"
        )

        if not isinstance(
            selections,
            list,
        ):

            raise ValueError(
                "Settlement selections list olmalıdır."
            )

        for selection in selections:

            if not isinstance(
                selection,
                dict,
            ):

                raise ValueError(
                    "Settlement selection dictionary olmalıdır."
                )

            outcome = str(
                selection.get(
                    "outcome",
                    "",
                )
            ).strip().upper()

            settlement_result = str(
                selection.get(
                    "settlement",
                    "",
                )
            ).strip().upper()

            if not outcome:

                raise ValueError(
                    "Settlement selection outcome "
                    "boş olamaz."
                )

            if settlement_result not in {
                "WIN",
                "LOSS",
                "VOID",
            }:

                raise ValueError(
                    "Geçersiz settlement sonucu: "
                    f"{selection.get('settlement')}"
                )

            if settlement_result == "VOID":

                void_predictions += 1

                continue

            probability = _prediction_probability(
                record,
                outcome,
            )

            if probability is None:

                missing_probability_predictions += 1

                continue

            observations.append(
                CalibrationObservation(
                    market=outcome,
                    predicted_probability=(
                        probability
                    ),
                    actual=(
                        1
                        if settlement_result == "WIN"
                        else 0
                    ),
                )
            )

    return (
        observations,
        void_predictions,
        missing_probability_predictions,
    )


def calibration_summary(
    history,
) -> CalibrationSummary:
    """
    History için genel calibration metriklerini hesaplar.

    Brier Score:

        mean((prediction - actual)^2)

    Log Loss:

        -mean(
            actual * log(p)
            + (1-actual) * log(1-p)
        )
    """

    _validate_history(
        history
    )

    (
        observations,
        voids,
        missing,
    ) = collect_observations(
        history
    )

    evaluated = len(
        observations
    )

    total_predictions = (
        evaluated
        + voids
        + missing
    )

    if evaluated == 0:

        return CalibrationSummary(
            total_predictions=(
                total_predictions
            ),
            evaluated_predictions=0,
            void_predictions=voids,
            missing_probability_predictions=(
                missing
            ),
            brier_score=0.0,
            log_loss=0.0,
            mean_predicted_probability=0.0,
            empirical_win_rate=0.0,
        )

    brier_score = sum(
        (
            observation.predicted_probability
            - observation.actual
        )
        ** 2
        for observation in observations
    ) / evaluated

    epsilon = 1e-15

    log_loss = -sum(
        observation.actual
        * math.log(
            max(
                observation.predicted_probability,
                epsilon,
            )
        )
        + (
            1
            - observation.actual
        )
        * math.log(
            max(
                1.0
                - observation.predicted_probability,
                epsilon,
            )
        )
        for observation in observations
    ) / evaluated

    mean_probability = sum(
        observation.predicted_probability
        for observation in observations
    ) / evaluated

    empirical_win_rate = sum(
        observation.actual
        for observation in observations
    ) / evaluated

    return CalibrationSummary(
        total_predictions=(
            total_predictions
        ),
        evaluated_predictions=(
            evaluated
        ),
        void_predictions=voids,
        missing_probability_predictions=(
            missing
        ),
        brier_score=brier_score,
        log_loss=log_loss,
        mean_predicted_probability=(
            mean_probability
        ),
        empirical_win_rate=(
            empirical_win_rate
        ),
    )


def calibration_buckets(
    history,
    bucket_count: int = 10,
) -> list[CalibrationBucket]:
    """
    Tahmin olasılıklarını eşit genişlikte bucket'lara ayırır.

    Varsayılan:

        0.00-0.10
        0.10-0.20
        ...
        0.90-1.00
    """

    if (
        isinstance(
            bucket_count,
            bool,
        )
        or not isinstance(
            bucket_count,
            int,
        )
    ):

        raise TypeError(
            "bucket_count integer olmalıdır."
        )

    if bucket_count <= 0:

        raise ValueError(
            "bucket_count pozitif olmalıdır."
        )

    observations, _, _ = (
        collect_observations(
            history
        )
    )

    width = (
        1.0
        / bucket_count
    )

    buckets: list[
        CalibrationBucket
    ] = []

    for index in range(
        bucket_count
    ):

        lower = (
            index
            * width
        )

        upper = (
            1.0
            if index
            == bucket_count - 1
            else (
                index + 1
            )
            * width
        )

        selected = [
            observation
            for observation in observations
            if (
                observation.predicted_probability
                >= lower
                and (
                    observation.predicted_probability
                    < upper
                    or (
                        index
                        == bucket_count - 1
                        and observation.predicted_probability
                        <= upper
                    )
                )
            )
        ]

        predictions = len(
            selected
        )

        wins = sum(
            observation.actual
            for observation in selected
        )

        mean_probability = (
            sum(
                observation.predicted_probability
                for observation in selected
            )
            / predictions
            if predictions
            else 0.0
        )

        empirical_win_rate = (
            wins
            / predictions
            if predictions
            else 0.0
        )

        buckets.append(
            CalibrationBucket(
                lower_bound=lower,
                upper_bound=upper,
                predictions=predictions,
                wins=wins,
                mean_predicted_probability=(
                    mean_probability
                ),
                empirical_win_rate=(
                    empirical_win_rate
                ),
            )
        )

    return buckets


def calibration_by_market(
    history,
) -> dict[str, CalibrationSummary]:
    """
    Calibration metriklerini market outcome bazında hesaplar.

    Örnek:

        HOME
        DRAW
        AWAY
        OVER_2.5
        UNDER_2.5
        BTTS_YES
        BTTS_NO
    """

    observations, _, _ = (
        collect_observations(
            history
        )
    )

    grouped: dict[
        str,
        list[CalibrationObservation],
    ] = {}

    for observation in observations:

        grouped.setdefault(
            observation.market,
            [],
        ).append(
            observation
        )

    result: dict[
        str,
        CalibrationSummary,
    ] = {}

    for market in sorted(
        grouped
    ):

        group = grouped[
            market
        ]

        count = len(
            group
        )

        brier_score = sum(
            (
                observation.predicted_probability
                - observation.actual
            )
            ** 2
            for observation in group
        ) / count

        epsilon = 1e-15

        log_loss = -sum(
            observation.actual
            * math.log(
                max(
                    observation.predicted_probability,
                    epsilon,
                )
            )
            + (
                1
                - observation.actual
            )
            * math.log(
                max(
                    1.0
                    - observation.predicted_probability,
                    epsilon,
                )
            )
            for observation in group
        ) / count

        mean_probability = sum(
            observation.predicted_probability
            for observation in group
        ) / count

        empirical_win_rate = sum(
            observation.actual
            for observation in group
        ) / count

        result[
            market
        ] = CalibrationSummary(
            total_predictions=count,
            evaluated_predictions=count,
            void_predictions=0,
            missing_probability_predictions=0,
            brier_score=brier_score,
            log_loss=log_loss,
            mean_predicted_probability=(
                mean_probability
            ),
            empirical_win_rate=(
                empirical_win_rate
            ),
        )

    return result
