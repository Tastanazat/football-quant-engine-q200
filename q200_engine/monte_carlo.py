"""
Q200 Engine - Monte Carlo

Q200 V3.1

Monte Carlo maç simülasyon katmanı.

Kurallar:
- Minimum 100.000 iterasyon
- Negatif lambda kabul edilmez
- HOME / DRAW / AWAY olasılıkları döndürülür
- Seed verilmezse dahi girdilerden deterministik olarak
  türetilir: AYNI (lambda_home, lambda_away, iterations)
  girdisi HER ZAMAN AYNI sonucu üretir. İsteğe bağlı
  seed ile de tekrarlanabilir sonuç zorlanabilir.
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Optional


# =========================================================
# CONSTANTS
# =========================================================

MIN_ITERATIONS = 100_000


# =========================================================
# VALIDATION
# =========================================================

def _validate_lambda(value: float, name: str) -> float:
    """
    Lambda değerini doğrular.
    """

    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{name} sayısal olmalıdır."
        ) from exc

    if not math.isfinite(value):
        raise ValueError(
            f"{name} sonlu bir sayı olmalıdır."
        )

    if value < 0:
        raise ValueError(
            f"{name} negatif olamaz."
        )

    return value


def _validate_iterations(iterations: int) -> int:
    """
    Monte Carlo iterasyon sayısını doğrular.
    """

    if isinstance(iterations, bool):
        raise TypeError(
            "iterations integer olmalıdır."
        )

    if not isinstance(iterations, int):
        raise TypeError(
            "iterations integer olmalıdır."
        )

    if iterations < MIN_ITERATIONS:
        raise ValueError(
            "Monte Carlo minimum 100000 iteration olmalıdır."
        )

    return iterations


# =========================================================
# DETERMINISTIC SEED
# =========================================================

def _derive_seed(
    lambda_home: float,
    lambda_away: float,
    iterations: int,
) -> int:
    """
    Girdilerden deterministik bir seed türetir.

    Aynı (lambda_home, lambda_away, iterations) üçlüsü
    HER ZAMAN aynı seed'i, dolayısıyla aynı Monte Carlo
    sonucunu üretir. Farklı maçlar (farklı lambda'lar)
    farklı seed alır, bu yüzden simülasyonlar arasında
    yapay bir korelasyon oluşmaz.

    `random.Random.seed` int/hash tabanlı Python
    çalıştırmaları arasında (PYTHONHASHSEED farkı gibi
    nedenlerle) değişebildiği için burada hashlib
    kullanılır; bu, süreçler ve makineler arasında
    kararlıdır.
    """

    key = (
        f"{lambda_home:.12f}:"
        f"{lambda_away:.12f}:"
        f"{iterations}"
    ).encode("utf-8")

    digest = hashlib.sha256(key).hexdigest()

    # 64 bit'lik kararlı bir tamsayı seed.
    return int(digest[:16], 16)


# =========================================================
# POISSON RANDOM
# =========================================================

def _sample_poisson(
    lam: float,
    rng: Optional[random.Random] = None,
) -> int:
    """
    Poisson dağılımından rastgele değer üretir.

    Knuth algoritması kullanılır.

    Args:
        lam:
            Poisson lambda değeri.

        rng:
            İsteğe bağlı random generator.

    Returns:
        Poisson dağılımından üretilen gol sayısı.
    """

    lam = _validate_lambda(lam, "lambda")

    if rng is None:
        rng = random

    if lam == 0:
        return 0

    limit = math.exp(-lam)

    product = 1.0
    k = 0

    while product > limit:
        k += 1
        product *= rng.random()

    return k - 1


# =========================================================
# SIMULATION
# =========================================================

def simulate_match(
    lambda_home: float,
    lambda_away: float,
    iterations: int = MIN_ITERATIONS,
    seed: Optional[int] = None,
) -> dict[str, float]:
    """
    HOME / DRAW / AWAY Monte Carlo simülasyonu.

    Args:
        lambda_home:
            Ev sahibi gol beklentisi.

        lambda_away:
            Deplasman gol beklentisi.

        iterations:
            Simülasyon sayısı.
            Minimum 100.000 olmalıdır.

        seed:
            İsteğe bağlı random seed.
            Belirtilmezse (None), lambda_home / lambda_away /
            iterations değerlerinden deterministik olarak
            türetilir. Böylece AYNI GİRDİLER HER ZAMAN AYNI
            SONUCU üretir; farklı seed zorlamak isteyen
            çağıranlar bu parametreyi elle geçebilir
            (ör. duyarlılık/stres testleri için).

    Returns:
        {
            "HOME": float,
            "DRAW": float,
            "AWAY": float,
        }

    Örnek:

        result = simulate_match(
            1.50,
            1.10,
            iterations=100_000,
            seed=42,
        )
    """

    lambda_home = _validate_lambda(
        lambda_home,
        "lambda_home",
    )

    lambda_away = _validate_lambda(
        lambda_away,
        "lambda_away",
    )

    iterations = _validate_iterations(
        iterations
    )

    # -----------------------------------------------------
    # RANDOM GENERATOR
    # -----------------------------------------------------

    if seed is not None:
        if isinstance(seed, bool) or not isinstance(
            seed, int
        ):
            raise TypeError(
                "seed integer olmalıdır."
            )

    else:
        # Deterministik seed: aynı girdi -> aynı sonuç.
        seed = _derive_seed(
            lambda_home,
            lambda_away,
            iterations,
        )

    rng = random.Random(seed)

    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    home_wins = 0
    draws = 0
    away_wins = 0

    # -----------------------------------------------------
    # MONTE CARLO
    # -----------------------------------------------------

    for _ in range(iterations):

        home_goals = _sample_poisson(
            lambda_home,
            rng,
        )

        away_goals = _sample_poisson(
            lambda_away,
            rng,
        )

        if home_goals > away_goals:
            home_wins += 1

        elif home_goals == away_goals:
            draws += 1

        else:
            away_wins += 1

    # -----------------------------------------------------
    # PROBABILITIES
    # -----------------------------------------------------

    home_probability = (
        home_wins / iterations
    )

    draw_probability = (
        draws / iterations
    )

    away_probability = (
        away_wins / iterations
    )

    # -----------------------------------------------------
    # NUMERICAL SAFETY
    # -----------------------------------------------------

    total = (
        home_probability
        + draw_probability
        + away_probability
    )

    if total <= 0:
        raise RuntimeError(
            "Monte Carlo probability toplamı geçersiz."
        )

    # Çok küçük floating-point sapmalarını
    # normalize ediyoruz.
    home_probability /= total
    draw_probability /= total
    away_probability /= total

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "HOME": home_probability,
        "DRAW": draw_probability,
        "AWAY": away_probability,
    }
