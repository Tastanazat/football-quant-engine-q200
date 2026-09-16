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
Model snapshot LOCK edildikten sonra immutable kalır.
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


class Q200Pipeline:
    """
    Q200 V3.1 ana analiz pipeline'ı.

    Kullanım:

        stats = TeamStats(
            2.0,
            1.2,
            1.5,
            1.8,
            1.1,
            1.0,
            1.4,
        )

        pipeline = Q200Pipeline(stats)

        result = pipeline.analyze_odds(
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            bankroll=50_000,
        )
    """

    VERSION = "Q200-V3.1"

    def __init__(self, stats: TeamStats):
        if not isinstance(stats, TeamStats):
            raise TypeError(
                "stats must be an instance of TeamStats"
            )

        self.stats = stats

        # =================================================
        # MODEL BUILD
        # =================================================

        self.snapshot: ModelSnapshot = build_model(stats)

        # =================================================
        # MODEL LOCK CHECK
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

    @property
    def lambda_home(self) -> float:
        """
        Ev takımının lambda değerini döndürür.
        """
        return self.snapshot.lambda_home

    @property
    def lambda_away(self) -> float:
        """
        Deplasman takımının lambda değerini döndürür.
        """
        return self.snapshot.lambda_away

    @property
    def probabilities(self) -> Dict[str, float]:
        """
        Model tarafından üretilen olasılıkları döndürür.

        ÖNEMLİ:
        Dönen değer snapshot içindeki model
        olasılıklarıdır.
        """
        return dict(self.snapshot.probabilities)

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
        Bu fonksiyon model snapshot'ını değiştirmez.

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
                    f"Invalid odds for {outcome}: {value}"
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

        for outcome, probability in (
            self.snapshot.probabilities.items()
        ):

            if probability > 0:
                fair_odds[outcome] = 1.0 / probability
            else:
                fair_odds[outcome] = float("inf")

        # =================================================
        # EV
        #
        # EV = probability * odds - 1
        # =================================================

        ev = {}

        for outcome, price in normalized_odds.items():

            probability = self.snapshot.probabilities.get(
                outcome
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

    Örnek:

        result = run_pipeline(
            stats,
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            50_000,
        )
    """

    pipeline = Q200Pipeline(stats)

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )
