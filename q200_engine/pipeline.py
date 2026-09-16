"""
Q200 Engine - Pipeline Layer

Q200 V3.1

Akış:

STATISTICS
    ↓
MODEL
    ↓
LAMBDA
    ↓
POISSON
    ↓
MONTE CARLO
    ↓
MODEL LOCK
    ↓
ODDS
    ↓
NO-VIG
    ↓
FAIR ODDS
    ↓
EV
    ↓
SELECTION
    ↓
KELLY

ÖNEMLİ:

Odds modeli değiştiremez.

Model snapshot LOCK edildikten sonra
model çıktıları değiştirilemez.
"""

from __future__ import annotations

from typing import Dict

from .schema import (
    TeamStats,
    ModelSnapshot,
    AnalysisResult,
)

from .model import build_model
from .odds import implied_probabilities
from .selection import select


# =========================================================
# PIPELINE
# =========================================================

class Q200Pipeline:
    """
    Q200 V3.1 ana analiz pipeline'ı.

    Model aşamasında:

        Statistics
            ↓
        Lambda
            ↓
        Poisson
            ↓
        Monte Carlo
            ↓
        LOCK

    Odds aşamasında:

        Odds
            ↓
        No-Vig
            ↓
        Fair Odds
            ↓
        EV
            ↓
        Selection
    """

    VERSION = "Q200-V3.1"

    def __init__(
        self,
        stats: TeamStats,
    ):
        # =================================================
        # INPUT VALIDATION
        # =================================================

        if not isinstance(stats, TeamStats):
            raise TypeError(
                "stats must be an instance of TeamStats"
            )

        self.stats = stats

        # =================================================
        # MODEL BUILD
        # =================================================

        self.snapshot: ModelSnapshot = build_model(
            stats
        )

        # =================================================
        # LOCK VALIDATION
        # =================================================

        if not self.snapshot.locked:
            raise RuntimeError(
                "Q200 model must be locked after build."
            )

    # =====================================================
    # MODEL
    # =====================================================

    @property
    def model_locked(self) -> bool:
        """
        Modelin LOCK durumunu döndürür.
        """

        return self.snapshot.locked

    # -----------------------------------------------------

    @property
    def lambda_home(self) -> float:
        """
        HOME lambda.
        """

        return self.snapshot.lambda_home

    # -----------------------------------------------------

    @property
    def lambda_away(self) -> float:
        """
        AWAY lambda.
        """

        return self.snapshot.lambda_away

    # -----------------------------------------------------

    @property
    def probabilities(self) -> Dict[str, float]:
        """
        Poisson model olasılıklarını döndürür.
        """

        return dict(
            self.snapshot.probabilities
        )

    # -----------------------------------------------------

    @property
    def monte_carlo_probabilities(
        self,
    ) -> Dict[str, float]:
        """
        Monte Carlo olasılıklarını döndürür.

        Minimum 100.000 simülasyon sonucu
        model snapshot içerisinde saklanır.
        """

        return dict(
            self.snapshot.monte_carlo_probabilities
        )

    # -----------------------------------------------------

    @property
    def monte_carlo_iterations(self) -> int:
        """
        Kullanılan Monte Carlo iterasyon sayısını
        döndürür.
        """

        return (
            self.snapshot.monte_carlo_iterations
        )

    # -----------------------------------------------------

    @property
    def model_version(self) -> str:
        """
        Model versiyonunu döndürür.
        """

        return self.snapshot.model_version

    # =====================================================
    # ODDS ANALYSIS
    # =====================================================

    def analyze_odds(
        self,
        odds: Dict[str, float],
        bankroll: float,
        uncertainty: str = "MEDIUM",
    ) -> AnalysisResult:
        """
        Odds analizini gerçekleştirir.

        ÖNEMLİ:

        Bu fonksiyon model snapshot'ını
        değiştiremez.

        Model LOCK edildikten sonra odds yalnızca
        analiz katmanında kullanılır.

        Args:

            odds:
                {
                    "HOME": 2.00,
                    "DRAW": 3.50,
                    "AWAY": 4.00
                }

            bankroll:
                Kullanılacak bankroll.

            uncertainty:
                LOW / MEDIUM / HIGH / VERY_HIGH
        """

        # =================================================
        # INPUT VALIDATION
        # =================================================

        if not isinstance(odds, dict):
            raise TypeError(
                "odds must be a dictionary"
            )

        if bankroll <= 0:
            raise ValueError(
                "bankroll must be greater than zero"
            )

        if not odds:
            raise ValueError(
                "odds cannot be empty"
            )

        normalized_odds = {
            str(key).upper(): float(value)
            for key, value in odds.items()
        }

        for outcome, value in normalized_odds.items():

            if value <= 1.0:
                raise ValueError(
                    f"Invalid odds for "
                    f"{outcome}: {value}"
                )

        # =================================================
        # SNAPSHOT BEFORE ODDS
        # =================================================

        snapshot_before = self.snapshot

        # =================================================
        # NO-VIG
        # =================================================

        no_vig = implied_probabilities(
            normalized_odds
        )

        # =================================================
        # FAIR ODDS
        # =================================================

        fair_odds = {}

        for (
            outcome,
            probability,
        ) in self.snapshot.probabilities.items():

            if probability > 0:

                fair_odds[outcome] = (
                    1.0 / probability
                )

            else:

                fair_odds[outcome] = (
                    float("inf")
                )

        # =================================================
        # EV
        # =================================================

        ev = {}

        for outcome, price in normalized_odds.items():

            probability = (
                self.snapshot.probabilities.get(
                    outcome
                )
            )

            if probability is None:
                continue

            ev[outcome] = (
                probability * price
            ) - 1.0

        # =================================================
        # SELECTION
        # =================================================

        selections = select(
            self.snapshot.probabilities,
            normalized_odds,
            bankroll,
            uncertainty=uncertainty,
        )

        # =================================================
        # MODEL IMMUTABILITY CHECK
        # =================================================

        if self.snapshot != snapshot_before:
            raise RuntimeError(
                "CRITICAL: odds analysis changed "
                "the locked model snapshot."
            )

        # =================================================
        # RESULT
        # =================================================

        return AnalysisResult(
            snapshot=self.snapshot,
            fair_odds=fair_odds,
            no_vig_probabilities=no_vig,
            ev=ev,
            selections=selections,
        )


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def run_pipeline(
    stats: TeamStats,
    odds: Dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Q200 pipeline'ı tek fonksiyonla çalıştırır.
    """

    pipeline = Q200Pipeline(stats)

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )
