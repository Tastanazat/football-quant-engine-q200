"""
Q200 Engine - Model Layer

Model oluşturma:
1. TeamStats verilerinden lambda HOME / AWAY hesaplanır.
2. Poisson dağılımı oluşturulur.
3. 1X2 olasılıkları hesaplanır.
4. Model çıktısı odds'tan bağımsızdır.

Odds bu dosyada KULLANILMAZ.
"""

from __future__ import annotations

from math import exp, factorial
from typing import Any, Dict, Tuple


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _get(obj: Any, *names: str, default: float = 0.0) -> float:
    """
    TeamStats nesnesinden farklı olası attribute isimlerini okur.
    Dict desteklenir.
    """
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return float(obj[name])
        return float(default)

    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return float(value)

    return float(default)


# ---------------------------------------------------------
# LAMBDA
# ---------------------------------------------------------

def calculate_lambdas(stats: Any) -> Tuple[float, float]:
    """
    Q200 V3.x lambda hesaplaması.

    FORMÜL:

    HOME =
        0.35 * Home Home GF
      + 0.35 * Away Away GA
      + 0.15 * Home Home xG
      + 0.15 * Away Away xGA

    AWAY =
        0.35 * Away Away GF
      + 0.35 * Home Home GA
      + 0.15 * Away Away xG
      + 0.15 * Home Home xGA

    xG/xGA mevcut değilse ağırlıklar GF/GA tarafına
    normalize edilir.
    """

    # -------------------------
    # HOME TEAM
    # -------------------------

    home_gf = _get(
        stats,
        "home_home_gf",
        "home_gf",
        "homeGF",
        "home_goals_for",
    )

    home_ga = _get(
        stats,
        "home_home_ga",
        "home_ga",
        "homeGA",
        "home_goals_against",
    )

    home_xg = _get(
        stats,
        "home_home_xg",
        "home_xg",
        "homeXG",
        default=0.0,
    )

    home_xga = _get(
        stats,
        "home_home_xga",
        "home_xga",
        "homeXGA",
        default=0.0,
    )

    # -------------------------
    # AWAY TEAM
    # -------------------------

    away_gf = _get(
        stats,
        "away_away_gf",
        "away_gf",
        "awayGF",
        "away_goals_for",
    )

    away_ga = _get(
        stats,
        "away_away_ga",
        "away_ga",
        "awayGA",
        "away_goals_against",
    )

    away_xg = _get(
        stats,
        "away_away_xg",
        "away_xg",
        "awayXG",
        default=0.0,
    )

    away_xga = _get(
        stats,
        "away_away_xga",
        "away_xga",
        "awayXGA",
        default=0.0,
    )

    # -------------------------------------------------
    # xG bilgisi gerçekten mevcut mu?
    # -------------------------------------------------

    xg_available = (
        home_xg > 0
        or home_xga > 0
        or away_xg > 0
        or away_xga > 0
    )

    if xg_available:
        lambda_home = (
            0.35 * home_gf
            + 0.35 * away_ga
            + 0.15 * home_xg
            + 0.15 * away_xga
        )

        lambda_away = (
            0.35 * away_gf
            + 0.35 * home_ga
            + 0.15 * away_xg
            + 0.15 * home_xga
        )

    else:
        # xG yoksa 35% + 35% = %70'lik GF/GA ağırlığını
        # %100'e normalize ediyoruz.
        lambda_home = (
            0.50 * home_gf
            + 0.50 * away_ga
        )

        lambda_away = (
            0.50 * away_gf
            + 0.50 * home_ga
        )

    # Güvenli sınırlar
    lambda_home = max(0.01, float(lambda_home))
    lambda_away = max(0.01, float(lambda_away))

    return lambda_home, lambda_away


# ---------------------------------------------------------
# POISSON
# ---------------------------------------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """Poisson olasılığı."""
    if k < 0:
        return 0.0

    return exp(-lam) * (lam ** k) / factorial(k)


def build_score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
):
    """
    Ev sahibi / deplasman skor olasılık matrisi.
    """

    home_probs = [
        poisson_pmf(i, lambda_home)
        for i in range(max_goals + 1)
    ]

    away_probs = [
        poisson_pmf(i, lambda_away)
        for i in range(max_goals + 1)
    ]

    matrix = []

    for h in range(max_goals + 1):
        row = []

        for a in range(max_goals + 1):
            row.append(home_probs[h] * away_probs[a])

        matrix.append(row)

    return matrix


# ---------------------------------------------------------
# 1X2 PROBABILITIES
# ---------------------------------------------------------

def probabilities_from_lambdas(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[str, float]:

    matrix = build_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    home = 0.0
    draw = 0.0
    away = 0.0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):

            p = matrix[h][a]

            if h > a:
                home += p

            elif h == a:
                draw += p

            else:
                away += p

    total = home + draw + away

    if total <= 0:
        raise ValueError("Model probabilities could not be calculated.")

    home /= total
    draw /= total
    away /= total

    return {
        "HOME": home,
        "DRAW": draw,
        "AWAY": away,
    }


# ---------------------------------------------------------
# MODEL BUILDER
# ---------------------------------------------------------

def build_model(
    stats: Any,
    max_goals: int = 10,
) -> Dict[str, Any]:
    """
    Stats -> locked model output.

    ÖNEMLİ:
    Odds bu fonksiyona girmez.
    Böylece model odds'tan bağımsız kalır.
    """

    lambda_home, lambda_away = calculate_lambdas(stats)

    probabilities = probabilities_from_lambdas(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    score_matrix = build_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    return {
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "probabilities": probabilities,
        "score_matrix": score_matrix,
        "max_goals": max_goals,
        "model_locked": True,
    }


# ---------------------------------------------------------
# BACKWARD COMPATIBILITY
# ---------------------------------------------------------

def model_probabilities(stats: Any) -> Dict[str, float]:
    """
    Eski kodlar için yardımcı fonksiyon.
    """
    model = build_model(stats)

    return model["probabilities"]
