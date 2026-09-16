"""
Q200 Engine - Markets Layer

Q200 V3.1

Market olasılıklarını model lambda değerlerinden üretir.

Desteklenen marketler:
- 1X2
- Over / Under 0.5
- Over / Under 1.5
- Over / Under 2.5
- Over / Under 3.5
- BTTS
- Correct Score

ÖNEMLİ:
Bu katman oran kullanmaz.
Sadece modelden gelen lambda değerleriyle çalışır.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple


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


# =========================================================
# POISSON PMF
# =========================================================

def poisson_probability(goals: int, lam: float) -> float:
    """
    Belirli sayıda gol için Poisson olasılığı.

    P(X=k) = e^-lambda * lambda^k / k!
    """

    _validate_lambda(lam, "lambda")

    if goals < 0:
        raise ValueError("Gol sayısı negatif olamaz.")

    if not isinstance(goals, int):
        raise TypeError("Gol sayısı integer olmalıdır.")

    if lam == 0:
        return 1.0 if goals == 0 else 0.0

    return math.exp(-lam) * (lam ** goals) / math.factorial(goals)


# =========================================================
# GOAL DISTRIBUTION
# =========================================================

def goal_distribution(
    lam: float,
    max_goals: int = 10,
) -> Dict[int, float]:
    """
    0..max_goals arasındaki gol olasılıklarını üretir.

    Kuyruk kaybını azaltmak için son hücreye kalan
    olasılık eklenir.
    """

    _validate_lambda(lam, "lambda")

    if max_goals < 1:
        raise ValueError("max_goals en az 1 olmalıdır.")

    probabilities = {
        goals: poisson_probability(goals, lam)
        for goals in range(max_goals + 1)
    }

    total = sum(probabilities.values())

    if total <= 0:
        raise ValueError("Geçersiz Poisson dağılımı.")

    # Sayısal yuvarlama / tail düzeltmesi.
    # max_goals hücresini normalize ediyoruz.
    return {
        goals: probability / total
        for goals, probability in probabilities.items()
    }


# =========================================================
# SCORE MATRIX
# =========================================================

def score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[Tuple[int, int], float]:
    """
    Ev ve deplasman gol dağılımlarından skor matrisi üretir.

    Anahtar:
        (home_goals, away_goals)

    Örnek:
        (2, 1) -> 2-1 olasılığı
    """

    _validate_lambda(lambda_home, "lambda_home")
    _validate_lambda(lambda_away, "lambda_away")

    home = goal_distribution(lambda_home, max_goals)
    away = goal_distribution(lambda_away, max_goals)

    matrix: Dict[Tuple[int, int], float] = {}

    for home_goals, home_probability in home.items():
        for away_goals, away_probability in away.items():
            matrix[(home_goals, away_goals)] = (
                home_probability * away_probability
            )

    return matrix


# =========================================================
# 1X2
# =========================================================

def match_result_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[str, float]:
    """
    1X2 model olasılıkları.

    HOME = Ev sahibi kazanır
    DRAW = Beraberlik
    AWAY = Deplasman kazanır
    """

    matrix = score_matrix(
        lambda_home,
        lambda_away,
        max_goals,
    )

    home = 0.0
    draw = 0.0
    away = 0.0

    for (home_goals, away_goals), probability in matrix.items():

        if home_goals > away_goals:
            home += probability

        elif home_goals == away_goals:
            draw += probability

        else:
            away += probability

    total = home + draw + away

    return {
        "HOME": home / total,
        "DRAW": draw / total,
        "AWAY": away / total,
    }


# =========================================================
# TOTAL GOALS
# =========================================================

def total_goals_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[str, float]:
    """
    Toplam gol marketleri.

    Örnek:
        OVER_2.5
        UNDER_2.5
    """

    matrix = score_matrix(
        lambda_home,
        lambda_away,
        max_goals,
    )

    result: Dict[str, float] = {}

    lines = (
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
        5.5,
    )

    for line in lines:

        over = sum(
            probability
            for (home_goals, away_goals), probability
            in matrix.items()
            if home_goals + away_goals > line
        )

        under = sum(
            probability
            for (home_goals, away_goals), probability
            in matrix.items()
            if home_goals + away_goals < line
        )

        total = over + under

        if total > 0:
            over /= total
            under /= total

        result[f"OVER_{line}"] = over
        result[f"UNDER_{line}"] = under

    return result


# =========================================================
# BTTS
# =========================================================

def btts_probabilities(
    lambda_home: float,
    lambda_away: float,
) -> Dict[str, float]:
    """
    Both Teams To Score.

    BTTS_YES:
        Ev sahibi en az 1 gol
        VE
        Deplasman en az 1 gol

    BTTS_NO:
        Takımlardan en az biri gol atamaz.
    """

    _validate_lambda(lambda_home, "lambda_home")
    _validate_lambda(lambda_away, "lambda_away")

    home_zero = poisson_probability(0, lambda_home)
    away_zero = poisson_probability(0, lambda_away)

    btts_yes = (
        (1.0 - home_zero)
        * (1.0 - away_zero)
    )

    btts_no = 1.0 - btts_yes

    return {
        "BTTS_YES": btts_yes,
        "BTTS_NO": btts_no,
    }


# =========================================================
# CORRECT SCORE
# =========================================================

def correct_score_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 6,
) -> Dict[str, float]:
    """
    Doğru skor olasılıklarını üretir.

    Örnek:
        "0-0"
        "1-0"
        "1-1"
        "2-1"
        "2-2"
    """

    matrix = score_matrix(
        lambda_home,
        lambda_away,
        max_goals,
    )

    return {
        f"{home_goals}-{away_goals}": probability
        for (home_goals, away_goals), probability
        in matrix.items()
    }


# =========================================================
# ALL MARKETS
# =========================================================

def all_market_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[str, float]:
    """
    Q200 market motorunun ana fonksiyonu.

    Model lambda değerlerinden bütün temel marketleri
    tek sözlükte toplar.

    Odds kullanılmaz.
    """

    result: Dict[str, float] = {}

    # 1X2
    result.update(
        match_result_probabilities(
            lambda_home,
            lambda_away,
            max_goals,
        )
    )

    # Over / Under
    result.update(
        total_goals_probabilities(
            lambda_home,
            lambda_away,
            max_goals,
        )
    )

    # BTTS
    result.update(
        btts_probabilities(
            lambda_home,
            lambda_away,
        )
    )

    return result


# =========================================================
# FAIR ODDS
# =========================================================

def fair_odds_from_probabilities(
    probabilities: Dict[str, float],
) -> Dict[str, float]:
    """
    Model olasılığından fair odds hesaplar.

    Fair Odds = 1 / Model Probability

    0 olasılıklı marketler atlanır.
    """

    fair_odds: Dict[str, float] = {}

    for market, probability in probabilities.items():

        if probability <= 0:
            continue

        if probability > 1:
            raise ValueError(
                f"{market} olasılığı 1'den büyük olamaz."
            )

        fair_odds[market] = 1.0 / probability

    return fair_odds
