"""
Q200 Engine - Analysis Runner

Q200 V3.1

Amaç
-----
FiveSourceMatchInput üzerinden Q200 analizini
tek bir giriş noktasıyla çalıştırmak.

Akış:

FiveSourceMatchInput
        ↓
Source Mapper
        ↓
Canonical / TeamStats
        ↓
Q200Pipeline
        ↓
MODEL
        ↓
MODEL LOCK
        ↓
STRESS TEST
        ↓
ODDS
        ↓
NO-VIG
        ↓
FAIR ODDS
        ↓
BASELINE EV
        ↓
PESSIMISTIC EV
        ↓
SELECTION
        ↓
KELLY

KRİTİK KURAL
------------
Bu katman model hesaplamaz.

Model hesaplama Q200Pipeline tarafından yapılır.

Odds model oluşturulmadan önce kullanılmaz.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .pipeline import (
    Q200Pipeline,
)
from .schema import (
    AnalysisResult,
    TeamStats,
)


RUNNER_VERSION = "Q200-ANALYSIS-RUNNER-V2"


@dataclass(frozen=True)
class AnalysisRun:
    """
    Tek bir Q200 analiz çalışmasının sonucu.

    raw_result:
        Mevcut Q200 AnalysisResult.

    metadata:
        Çalıştırma bilgileri.
    """

    result: AnalysisResult
    metadata: dict[str, Any]


def _validate_bankroll(
    bankroll: float,
) -> float:
    """
    Bankroll değerini doğrular.
    """

    try:
        value = float(bankroll)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "bankroll sayısal olmalıdır."
        ) from exc

    if value <= 0:
        raise ValueError(
            "bankroll pozitif olmalıdır."
        )

    return value


def _validate_odds(
    odds: dict[str, float],
) -> dict[str, float]:
    """
    Odds sözlüğünü normalize eder.

    Pipeline'daki aynı doğrulama kurallarını
    burada önceden kontrol eder.

    Model bu aşamada oluşturulmaz.
    """

    if not isinstance(
        odds,
        dict,
    ):
        raise TypeError(
            "odds dictionary olmalıdır."
        )

    if not odds:
        raise ValueError(
            "odds boş olamaz."
        )

    normalized: dict[str, float] = {}

    for outcome, odd in odds.items():

        key = str(
            outcome
        ).upper()

        try:
            value = float(
                odd
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Geçersiz odds: "
                f"{outcome}={odd}"
            ) from exc

        if value <= 1.0:
            raise ValueError(
                f"Odds 1.0'dan büyük "
                f"olmalıdır: {outcome}"
            )

        normalized[key] = value

    return normalized


def run_analysis(
    *,
    stats: TeamStats,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisRun:
    """
    Q200 V3.1 tam analiz çalıştırıcısı.

    Parameters
    ----------
    stats:
        Model oluşturmak için TeamStats.

    odds:
        Analiz edilecek gerçek market odds'ları.

    bankroll:
        Kelly / selection hesabında kullanılacak bankroll.

    uncertainty:
        Q200 uncertainty seviyesi.

    Returns
    -------
    AnalysisRun
        Q200 AnalysisResult ve metadata.

    KRİTİK:
        Model önce oluşturulur.
        Pipeline içinde LOCK edilir.
        Daha sonra odds analizi yapılır.
    """

    if not isinstance(
        stats,
        TeamStats,
    ):
        raise TypeError(
            "stats TeamStats olmalıdır."
        )

    normalized_odds = _validate_odds(
        odds
    )

    validated_bankroll = (
        _validate_bankroll(
            bankroll
        )
    )

    pipeline = Q200Pipeline(
        stats
    )

    if not pipeline.model_locked:
        raise RuntimeError(
            "Q200 modeli LOCK edilmedi."
        )

    result = pipeline.analyze_odds(
        odds=normalized_odds,
        bankroll=validated_bankroll,
        uncertainty=uncertainty,
    )

    if not result.snapshot.locked:
        raise RuntimeError(
            "Analiz sonucu LOCK edilmiş "
            "model içermiyor."
        )

    return AnalysisRun(
        result=result,
        metadata={
            "runner_version": RUNNER_VERSION,
            "pipeline_version": (
                pipeline.VERSION
            ),
            "model_locked": True,
            "odds_used_after_model_lock": True,
            "uncertainty": uncertainty,
        },
    )


def run_from_pipeline(
    *,
    pipeline: Q200Pipeline,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisRun:
    """
    Önceden oluşturulmuş Q200Pipeline üzerinden
    analiz çalıştırır.

    Bu fonksiyon özellikle test ve üst seviye
    entegrasyonlar için kullanılır.

    Pipeline'ın mevcut snapshot'ı korunur.
    """

    if not isinstance(
        pipeline,
        Q200Pipeline,
    ):
        raise TypeError(
            "pipeline Q200Pipeline olmalıdır."
        )

    if not pipeline.model_locked:
        raise RuntimeError(
            "Pipeline modeli LOCK edilmemiş."
        )

    normalized_odds = _validate_odds(
        odds
    )

    validated_bankroll = (
        _validate_bankroll(
            bankroll
        )
    )

    snapshot_before = (
        pipeline.snapshot
    )

    result = pipeline.analyze_odds(
        odds=normalized_odds,
        bankroll=validated_bankroll,
        uncertainty=uncertainty,
    )

    if pipeline.snapshot != snapshot_before:
        raise RuntimeError(
            "Analiz sırasında model snapshot "
            "değişti."
        )

    if not result.snapshot.locked:
        raise RuntimeError(
            "Analiz sonucu LOCK edilmiş "
            "model içermiyor."
        )

    return AnalysisRun(
        result=result,
        metadata={
            "runner_version": RUNNER_VERSION,
            "pipeline_version": (
                pipeline.VERSION
            ),
            "model_locked": True,
            "odds_used_after_model_lock": True,
            "uncertainty": uncertainty,
            "existing_pipeline": True,
        },
    )


__all__ = [
    "RUNNER_VERSION",
    "AnalysisRun",
    "run_analysis",
    "run_from_pipeline",
]
