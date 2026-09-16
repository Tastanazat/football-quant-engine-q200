"""
Q200 Engine - Markets Layer

Q200 V3.1

Market / odds katmanı.

ÖNEMLİ:
- Bu modül model oluşturmaz.
- Lambda değerlerini değiştirmez.
- Model Snapshot'ını değiştirmez.
- Odds yalnızca model LOCK edildikten sonra kullanılır.
- Vig / No-Vig
- Fair Odds
- EV
- Value
hesaplamalarını gerçekleştirir.
"""

from __future__ import annotations

from typing import Dict


# =========================================================
# CONSTANTS
# =========================================================

MIN_ODDS = 1.50


# =========================================================
# VALIDATION
# =========================================================

def validate_odds(
    odds: Dict[str, float],
) -> None:
    """
    Oranların geçerli olup olmadığını kontrol eder.
    """

    if not isinstance(odds, dict):
        raise TypeError(
            "odds bir dictionary olmalıdır."
        )

    if not odds:
        raise ValueError(
            "Odds boş olamaz."
        )

    for outcome, odd in odds.items():

        if not isinstance(outcome, str):
            raise TypeError(
                "Market outcome anahtarı string olmalıdır."
            )

        if not isinstance(odd, (int, float)):
            raise TypeError(
                f"{outcome} oranı sayısal olmalıdır."
            )

        if odd <= 1.0:
            raise ValueError(
                f"{outcome} oranı 1.0'dan büyük olmalıdır."
            )


# =========================================================
# IMPLIED PROBABILITY
# =========================================================

def implied_probabilities(
    odds: Dict[str, float],
) -> Dict[str, float]:
    """
    Decimal odds -> implied probability.

    Formül:

        P = 1 / Odds
    """

    validate_odds(odds)

    return {
        outcome: 1.0 / odd
        for outcome, odd in odds.items()
    }


# =========================================================
# OVERROUND / VIG
# =========================================================

def calculate_overround(
    odds: Dict[str, float],
) -> float:
    """
    Bookmaker overround / vig hesaplar.

    Örnek:

        HOME 2.00
        DRAW 3.50
        AWAY 4.00

    implied probability toplamı > 1 ise
    aradaki fark bookmaker marginidir.

    Return:
        decimal değer

    Örnek:
        0.08 = %8
    """

    probabilities = implied_probabilities(odds)

    total_probability = sum(
        probabilities.values()
    )

    return total_probability - 1.0


# =========================================================
# NO-VIG PROBABILITIES
# =========================================================

def remove_vig(
    odds: Dict[str, float],
) -> Dict[str, float]:
    """
    Bookmaker marjını normalize ederek
    No-Vig probability üretir.

    Formül:

        NoVig P_i =
            P_i / sum(P)

    Böylece toplam:

        1.0

    olur.
    """

    probabilities = implied_probabilities(odds)

    total_probability = sum(
        probabilities.values()
    )

    if total_probability <= 0:
        raise ValueError(
            "Probability toplamı 0'dan büyük olmalıdır."
        )

    return {
        outcome: probability / total_probability
        for outcome, probability
        in probabilities.items()
    }


# =========================================================
# FAIR ODDS
# =========================================================

def fair_odds(
    probabilities: Dict[str, float],
) -> Dict[str, float]:
    """
    Model probability -> Fair Odds.

    Formül:

        Fair Odds = 1 / Probability
    """

    if not isinstance(probabilities, dict):
        raise TypeError(
            "probabilities dictionary olmalıdır."
        )

    result: Dict[str, float] = {}

    for outcome, probability in probabilities.items():

        if probability <= 0:
            result[outcome] = float("inf")

        else:
            result[outcome] = 1.0 / probability

    return result


# =========================================================
# EXPECTED VALUE
# =========================================================

def calculate_ev(
    probability: float,
    odds: float,
) -> float:
    """
    Expected Value hesaplar.

    Formül:

        EV = (Probability × Odds) - 1

    Örnek:

        Probability = 0.60
        Odds = 2.00

        EV = 0.60 × 2.00 - 1
           = 0.20

        = +20%
    """

    if probability < 0 or probability > 1:
        raise ValueError(
            "Probability 0 ile 1 arasında olmalıdır."
        )

    if odds <= 1:
        raise ValueError(
            "Odds 1'den büyük olmalıdır."
        )

    return (
        probability * odds
    ) - 1.0


# =========================================================
# EV FOR MARKET
# =========================================================

def calculate_market_ev(
    probabilities: Dict[str, float],
    odds: Dict[str, float],
) -> Dict[str, float]:
    """
    Model probability + odds kullanarak
    her outcome için EV hesaplar.

    Odds model oluşturmak için kullanılmaz.

    Burada yalnızca LOCK edilmiş model
    probability çıktısı kullanılır.
    """

    if not isinstance(
        probabilities,
        dict,
    ):
        raise TypeError(
            "probabilities dictionary olmalıdır."
        )

    validate_odds(odds)

    result: Dict[str, float] = {}

    for outcome, odd in odds.items():

        if outcome not in probabilities:
            continue

        probability = probabilities[
            outcome
        ]

        result[outcome] = calculate_ev(
            probability,
            odd,
        )

    return result


# =========================================================
# VALUE
# =========================================================

def calculate_value(
    model_probability: float,
    market_probability: float,
) -> float:
    """
    Model probability ile market probability
    arasındaki farkı hesaplar.

    Formül:

        Value =
            Model Probability
            - Market Probability

    Örnek:

        Model = 0.60
        Market = 0.50

        Value = +0.10
               = +10 percentage points
    """

    if not 0 <= model_probability <= 1:
        raise ValueError(
            "model_probability 0 ile 1 arasında olmalıdır."
        )

    if not 0 <= market_probability <= 1:
        raise ValueError(
            "market_probability 0 ile 1 arasında olmalıdır."
        )

    return (
        model_probability
        - market_probability
    )


# =========================================================
# MARKET ANALYSIS
# =========================================================

def analyze_market(
    model_probabilities: Dict[str, float],
    odds: Dict[str, float],
) -> dict:
    """
    Tam market analizi.

    Sıra:

        1. Odds validation
        2. Implied probability
        3. Vig
        4. No-Vig
        5. Fair Odds
        6. EV
        7. Value
    """

    validate_odds(odds)

    implied = implied_probabilities(
        odds
    )

    overround = calculate_overround(
        odds
    )

    no_vig = remove_vig(
        odds
    )

    fair = fair_odds(
        model_probabilities
    )

    ev = calculate_market_ev(
        model_probabilities,
        odds,
    )

    value = {}

    for outcome in odds:

        if outcome not in model_probabilities:
            continue

        value[outcome] = calculate_value(
            model_probabilities[outcome],
            no_vig[outcome],
        )

    return {
        "implied_probabilities": implied,
        "overround": overround,
        "no_vig_probabilities": no_vig,
        "fair_odds": fair,
        "ev": ev,
        "value": value,
    }


# =========================================================
# MINIMUM ODDS FILTER
# =========================================================

def filter_minimum_odds(
    odds: Dict[str, float],
    minimum_odds: float = MIN_ODDS,
) -> Dict[str, float]:
    """
    Minimum odds filtresi.

    Q200 V3.1:

        Minimum odds = 1.50
    """

    if minimum_odds <= 1.0:
        raise ValueError(
            "minimum_odds 1.0'dan büyük olmalıdır."
        )

    validate_odds(odds)

    return {
        outcome: odd
        for outcome, odd in odds.items()
        if odd >= minimum_odds
    }


# =========================================================
# EV THRESHOLD
# =========================================================

def ev_threshold(
    uncertainty: str,
) -> float | None:
    """
    Q200 V3.1 EV eşikleri.

    LOW:
        +5%

    MEDIUM:
        +8%

    HIGH:
        +12%

    VERY_HIGH:
        NO BET
    """

    normalized = uncertainty.upper().strip()

    thresholds = {
        "LOW": 0.05,
        "MEDIUM": 0.08,
        "HIGH": 0.12,
        "VERY_HIGH": None,
    }

    if normalized not in thresholds:
        raise ValueError(
            "Geçersiz uncertainty. "
            "LOW, MEDIUM, HIGH veya VERY_HIGH kullanın."
        )

    return thresholds[normalized]


# =========================================================
# EV FILTER
# =========================================================

def filter_by_ev(
    ev: Dict[str, float],
    uncertainty: str,
) -> Dict[str, float]:
    """
    Belirsizlik seviyesine göre EV filtresi uygular.

    VERY_HIGH:
        hiçbir seçim döndürmez.
    """

    threshold = ev_threshold(
        uncertainty
    )

    if threshold is None:
        return {}

    return {
        outcome: value
        for outcome, value in ev.items()
        if value >= threshold
    }
