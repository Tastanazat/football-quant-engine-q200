"""
Q200 Engine - Pipeline

Q200 V3.1

ANA AKIŞ:

Statistics
    ↓
Lambda
    ↓
Poisson Model
    ↓
Monte Carlo
    ↓
MODEL LOCK
    ↓
Odds
    ↓
No-Vig
    ↓
Fair Odds / EV / Selection

KRİTİK KURAL:

Odds, model oluşturulduktan sonra sisteme girer.

Odds hiçbir şekilde:
- lambda
- model probabilities
- score matrix
- Monte Carlo

değerlerini değiştiremez.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .model import (
    ModelSnapshot,
    build_model,
)

from .monte_carlo import (
    MIN_ITERATIONS,
    simulate_match,
)


class Q200Pipeline:
    """
    Q200 ana pipeline sınıfı.

    Stage 1:
        Statistics -> Model

    Stage 2:
        Model -> Monte Carlo

    Stage 3:
        Locked Model -> Odds
    """

    # =====================================================
    # INIT
    # =====================================================

    def __init__(
        self,
        stats: Any,
        monte_carlo_iterations: int = MIN_ITERATIONS,
    ) -> None:

        if monte_carlo_iterations < MIN_ITERATIONS:
            raise ValueError(
                "Monte Carlo requires at least "
                f"{MIN_ITERATIONS} iterations."
            )

        self.stats = stats

        self.monte_carlo_iterations = (
            monte_carlo_iterations
        )

        # -------------------------------------------------
        # MODEL
        # -------------------------------------------------

        self.snapshot: ModelSnapshot = build_model(
            stats
        )

        # -------------------------------------------------
        # MONTE CARLO
        # -------------------------------------------------

        self.monte_carlo_probabilities = (
            simulate_match(
                self.snapshot.lambda_home,
                self.snapshot.lambda_away,
                iterations=monte_carlo_iterations,
            )
        )

        # -------------------------------------------------
        # LOCK
        # -------------------------------------------------

        self._model_locked = True

        # Odds analysis sonucu
        self.analysis_result: Optional[Any] = None

    # =====================================================
    # MODEL LOCK
    # =====================================================

    @property
    def model_locked(self) -> bool:
        """
        Modelin LOCK durumunu döndürür.
        """

        return self._model_locked

    # =====================================================
    # MODEL PROBABILITIES
    # =====================================================

    @property
    def model_probabilities(self) -> Dict[str, float]:
        """
        LOCK edilmiş Poisson model olasılıkları.

        Odds tarafından değiştirilemez.
        """

        return dict(
            self.snapshot.probabilities
        )

    # =====================================================
    # MONTE CARLO PROBABILITIES
    # =====================================================

    @property
    def monte_carlo(self) -> Dict[str, float]:
        """
        Monte Carlo sonuçlarını döndürür.
        """

        return dict(
            self.monte_carlo_probabilities
        )

    # =====================================================
    # ODDS ANALYSIS
    # =====================================================

    def analyze_odds(
        self,
        odds: Dict[str, float],
        bankroll: float,
        uncertainty: str = "MEDIUM",
    ) -> Any:
        """
        Locked model üzerinde odds analizi başlatır.

        KRİTİK:

        Bu fonksiyon:
        - lambda değiştiremez
        - model probability değiştiremez
        - score matrix değiştiremez
        - Monte Carlo sonucunu değiştiremez

        Odds sadece sonraki aşamalarda kullanılır.
        """

        if not self._model_locked:
            raise RuntimeError(
                "Model must be locked before odds analysis."
            )

        # -------------------------------------------------
        # SNAPSHOT BEFORE
        # -------------------------------------------------

        snapshot_before = self.snapshot

        # -------------------------------------------------
        # ODDS
        # -------------------------------------------------

        from .odds import implied_probabilities

        no_vig = implied_probabilities(
            odds
        )

        # -------------------------------------------------
        # FAIR ODDS
        # -------------------------------------------------

        fair_odds = {}

        for outcome, probability in (
            self.snapshot.probabilities.items()
        ):

            if probability <= 0:

                fair_odds[outcome] = float("inf")

            else:

                fair_odds[outcome] = (
                    1.0 / probability
                )

        # -------------------------------------------------
        # EV
        # -------------------------------------------------

        ev = {}

        for outcome, probability in (
            self.snapshot.probabilities.items()
        ):

            if outcome not in odds:
                continue

            odd = float(odds[outcome])

            ev[outcome] = (
                probability * odd
            ) - 1.0

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        result = {
            "snapshot": snapshot_before,
            "model_probabilities": dict(
                self.snapshot.probabilities
            ),
            "monte_carlo_probabilities": dict(
                self.monte_carlo_probabilities
            ),
            "no_vig_probabilities": no_vig,
            "fair_odds": fair_odds,
            "ev": ev,
            "odds": dict(odds),
            "bankroll": float(bankroll),
            "uncertainty": uncertainty,
        }

        # -------------------------------------------------
        # INTEGRITY CHECK
        # -------------------------------------------------

        if self.snapshot != snapshot_before:

            raise RuntimeError(
                "MODEL LOCK VIOLATION: "
                "Odds changed the model snapshot."
            )

        self.analysis_result = result

        return result
