"""
Q200 Engine - Stress Test Layer

Q200 V3.1

Model belirsizliğini lambda değerleri üzerinden test eder.

ÖNEMLİ:
- Odds kullanılmaz.
- ModelSnapshot değiştirilmez.
- Stress test bağımsız senaryo üretir.
- Her senaryo Poisson dağılımını yeniden hesaplar.
"""

from __future__ import annotations

import math
from typing import Dict

from .markets import all_market_probabilities


# =========================================================
# DEFAULT SCENARIOS
# =========================================================

DEFAULT_MULTIPLIERS = {
    "OPTIMISTIC": {
        "HOME": 1.05,
        "AWAY": 0.95,
    },
    "BASELINE": {
        "HOME": 1.00,
        "AWAY": 1.00,
    },
    "PESSIMISTIC": {
        "HOME": 0.95,
        "AWAY": 1.05,
    },
}


# =========================================================
# VALIDATION
# =========================================================

def _validate_lambda(value: float, name: str) -> None:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} sayısal olmalıdır.")

    if not math.isfinite(value):
        raise ValueError(f"{name} sonlu bir sayı olmalıdır.")

    if value < 0:
        raise ValueError(f"{name} negatif olamaz.")


def _validate_multiplier(value: float, name: str) -> None:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} sayısal olmalıdır.")

    if not math.isfinite(value):
        raise ValueError(f"{name} sonlu bir sayı olmalıdır.")

    if value <= 0:
        raise ValueError(f"{name} sıfırdan büyük olmalıdır.")


# =========================================================
# SCENARIO LAMBDAS
# =========================================================

def stress_lambdas(
    lambda_home: float,
    lambda_away: float,
    multipliers: Dict[str, Dict[str, float]] | None = None,
) -> Dict[str, Dict[str, float]]:
    """
    Lambda değerlerinden stress senaryoları üretir.

    Varsayılan:

        OPTIMISTIC:
            HOME × 1.05
            AWAY × 0.95

        BASELINE:
            HOME × 1.00
            AWAY × 1.00

        PESSIMISTIC:
            HOME × 0.95
            AWAY × 1.05

    Returns:
        {
            "OPTIMISTIC": {
                "lambda_home": ...,
                "lambda_away": ...
            },
            ...
        }
    """

    _validate_lambda(lambda_home, "lambda_home")
    _validate_lambda(lambda_away, "lambda_away")

    scenarios = multipliers or DEFAULT_MULTIPLIERS

    results: Dict[str, Dict[str, float]] = {}

    for scenario, values in scenarios.items():

        scenario_name = str(scenario).upper()

        if not isinstance(values, dict):
            raise TypeError(
                f"{scenario_name} senaryosu dict olmalıdır."
            )

        if "HOME" not in values or "AWAY" not in values:
            raise ValueError(
                f"{scenario_name} HOME ve AWAY multiplier içermelidir."
            )

        home_multiplier = values["HOME"]
        away_multiplier = values["AWAY"]

        _validate_multiplier(
            home_multiplier,
            f"{scenario_name}.HOME",
        )

        _validate_multiplier(
            away_multiplier,
            f"{scenario_name}.AWAY",
        )

        results[scenario_name] = {
            "lambda_home": lambda_home * home_multiplier,
            "lambda_away": lambda_away * away_multiplier,
        }

    return results


# =========================================================
# STRESS MARKET PROBABILITIES
# =========================================================

def stress_market_probabilities(
    lambda_home: float,
    lambda_away: float,
    multipliers: Dict[str, Dict[str, float]] | None = None,
    max_goals: int = 10,
) -> Dict[str, Dict[str, float]]:
    """
    Her stress senaryosu için market olasılıklarını üretir.

    Odds kullanılmaz.

    Her senaryo kendi lambda değerlerinden yeniden
    Poisson market dağılımı üretir.
    """

    if not isinstance(max_goals, int):
        raise TypeError("max_goals integer olmalıdır.")

    if max_goals < 1:
        raise ValueError("max_goals en az 1 olmalıdır.")

    scenario_lambdas = stress_lambdas(
        lambda_home,
        lambda_away,
        multipliers,
    )

    results: Dict[str, Dict[str, float]] = {}

    for scenario, values in scenario_lambdas.items():

        results[scenario] = all_market_probabilities(
            values["lambda_home"],
            values["lambda_away"],
            max_goals=max_goals,
        )

    return results


# =========================================================
# SINGLE MARKET STRESS
# =========================================================

def stress_probability_range(
    lambda_home: float,
    lambda_away: float,
    market: str,
    multipliers: Dict[str, Dict[str, float]] | None = None,
    max_goals: int = 10,
) -> Dict[str, float]:
    """
    Tek bir market için stress senaryolarındaki
    olasılıkları döndürür.

    Örnek:

        stress_probability_range(
            1.5,
            1.1,
            "HOME",
        )

    Sonuç:

        {
            "OPTIMISTIC": ...,
            "BASELINE": ...,
            "PESSIMISTIC": ...
        }
    """

    market_name = str(market).upper()

    scenarios = stress_market_probabilities(
        lambda_home,
        lambda_away,
        multipliers,
        max_goals,
    )

    results: Dict[str, float] = {}

    for scenario, probabilities in scenarios.items():

        if market_name not in probabilities:
            raise KeyError(
                f"Market bulunamadı: {market_name}"
            )

        results[scenario] = probabilities[market_name]

    return results


# =========================================================
# ORIGINAL COMPATIBILITY FUNCTION
# =========================================================

def stress_probabilities(
    probabilities: Dict[str, float],
    multipliers=None,
):
    """
    Legacy compatibility wrapper.

    NOT:
    Eski sürüm bütün olasılıkları aynı katsayıyla çarpıyordu.
    Bu işlem normalize edildiğinde sonuç değişmediği için
    gerçek bir stress testi değildir.

    Bu fonksiyon eski API'nin kırılmaması için korunmuştur.

    Yeni kod için:
        stress_market_probabilities()
    kullanılmalıdır.
    """

    if not isinstance(probabilities, dict):
        raise TypeError("probabilities dict olmalıdır.")

    if not probabilities:
        raise ValueError("probabilities boş olamaz.")

    for outcome, probability in probabilities.items():

        if not isinstance(probability, (int, float)):
            raise TypeError(
                f"{outcome} olasılığı sayısal olmalıdır."
            )

        if not math.isfinite(probability):
            raise ValueError(
                f"{outcome} olasılığı sonlu olmalıdır."
            )

        if probability < 0 or probability > 1:
            raise ValueError(
                f"{outcome} olasılığı 0 ile 1 arasında olmalıdır."
            )

    multipliers = multipliers or {
        "OPTIMISTIC": 1.05,
        "BASELINE": 1.00,
        "PESSIMISTIC": 0.95,
    }

    results = {}

    for scenario, multiplier in multipliers.items():

        _validate_multiplier(
            multiplier,
            f"{scenario}.multiplier",
        )

        adjusted = {
            key: max(0.0, value * multiplier)
            for key, value in probabilities.items()
        }

        total = sum(adjusted.values())

        if total <= 0:
            raise ValueError(
                "Stress sonucunun toplam olasılığı sıfır olamaz."
            )

        results[str(scenario).upper()] = {
            key: value / total
            for key, value in adjusted.items()
        }

    return results
