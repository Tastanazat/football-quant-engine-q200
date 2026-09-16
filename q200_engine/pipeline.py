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

KRİTİK KURAL:

Odds model oluşturma aşamasında KULLANILMAZ.

Model snapshot LOCK edildikten sonra
odds analizi model parametrelerini değiştiremez.
"""

from __future__ import annotations

from math import isfinite
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
# CONSTANTS
# =========================================================

PIPELINE_VERSION = "Q200-V3.1"

VALID_UNCERTAINTY = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "VERY_HIGH",
}


# =========================================================
# Q200 PIPELINE
# =========================================================

class Q200Pipeline:
    """
    Q200 V3.1 ana analiz pipeline'ı.

    Stage 1:
        Statistics
            ↓
        Lambda
            ↓
        Poisson
            ↓
        Monte Carlo
            ↓
        Model Lock

    Stage 2:
        Odds
            ↓
        No-Vig
            ↓
        Fair Odds
            ↓
        EV
            ↓
        Selection
            ↓
        Kelly

    KRİTİK:
        Odds Stage 1'e hiçbir şekilde girmez.
    """

    VERSION = PIPELINE_VERSION

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, stats: TeamStats):
        """
        Pipeline oluşturur.

        Model burada oluşturulur ve LOCK edilir.
        """

        if not isinstance(stats, TeamStats):
            raise TypeError(
                "stats must be an instance of TeamStats"
            )

        self.stats = stats

        # -------------------------------------------------
        # STAGE 1
        # MODEL BUILD
        # -------------------------------------------------

        self.snapshot: ModelSnapshot = build_model(
            stats
        )

        # -------------------------------------------------
        # MODEL LOCK CHECK
        # -------------------------------------------------

        if not self.snapshot.locked:
            raise RuntimeError(
                "Q200 model must be locked after build."
            )

    # =====================================================
    # MODEL STATUS
    # =====================================================

    @property
    def model_locked(self) -> bool:
        """
        Model LOCK durumunu döndürür.
        """

        return bool(
            self.snapshot.locked
        )

    # =====================================================
    # LAMBDA
    # =====================================================

    @property
    def lambda_home(self) -> float:
        """
        Ev takımının lambda değerini döndürür.
        """

        return float(
            self.snapshot.lambda_home
        )

    @property
    def lambda_away(self) -> float:
        """
        Deplasman takımının lambda değerini döndürür.
        """

        return float(
            self.snapshot.lambda_away
        )

    # =====================================================
    # MODEL PROBABILITIES
    # =====================================================

    @property
    def probabilities(self) -> Dict[str, float]:
        """
        LOCK edilmiş model olasılıklarını döndürür.

        Odds tarafından değiştirilmez.
        """

        return dict(
            self.snapshot.probabilities
        )

    # =====================================================
    # MODEL VERSION
    # =====================================================

    @property
    def model_version(self) -> str:
        """
        Model versiyonunu döndürür.
        """

        return self.snapshot.model_version

    # =====================================================
    # ODDS VALIDATION
    # =====================================================

    @staticmethod
    def _validate_odds(
        odds: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Odds girişini doğrular ve normalize eder.
        """

        if not isinstance(odds, dict):
            raise TypeError(
                "odds must be a dictionary"
            )

        if not odds:
            raise ValueError(
                "odds cannot be empty"
            )

        normalized = {}

        for key, value in odds.items():

            outcome = str(key).upper().strip()

            try:
                price = float(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid odds for {outcome}: {value}"
                )

            if not isfinite(price):
                raise ValueError(
                    f"Odds must be finite for {outcome}"
                )

            if price <= 1.0:
                raise ValueError(
                    f"Invalid odds for {outcome}: {price}"
                )

            normalized[outcome] = price

        return normalized

    # =====================================================
    # UNCERTAINTY VALIDATION
    # =====================================================

    @staticmethod
    def _validate_uncertainty(
        uncertainty: str,
    ) -> str:
        """
        Belirsizlik seviyesini normalize eder.
        """

        if not isinstance(
            uncertainty,
            str,
        ):
            raise TypeError(
                "uncertainty must be a string"
            )

        normalized = (
            uncertainty
            .strip()
            .upper()
        )

        if normalized not in VALID_UNCERTAINTY:
            raise ValueError(
                "uncertainty must be one of: "
                "LOW, MEDIUM, HIGH, VERY_HIGH"
            )

        return normalized

    # =====================================================
    # BANKROLL VALIDATION
    # =====================================================

    @staticmethod
    def _validate_bankroll(
        bankroll: float,
    ) -> float:
        """
        Bankroll değerini doğrular.
        """

        try:
            value = float(bankroll)
        except (TypeError, ValueError):
            raise ValueError(
                "bankroll must be numeric"
            )

        if not isfinite(value):
            raise ValueError(
                "bankroll must be finite"
            )

        if value <= 0:
            raise ValueError(
                "bankroll must be greater than zero"
            )

        return value

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
        Stage 2 odds analizini gerçekleştirir.

        Akış:

            LOCKED MODEL
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

        KRİTİK:

        Bu fonksiyon model snapshot'ını değiştiremez.
        """

        # =================================================
        # INPUT VALIDATION
        # =================================================

        normalized_odds = self._validate_odds(
            odds
        )

        validated_bankroll = (
            self._validate_bankroll(
                bankroll
            )
        )

        normalized_uncertainty = (
            self._validate_uncertainty(
                uncertainty
            )
        )

        # =================================================
        # MODEL LOCK CHECK
        # =================================================

        if not self.snapshot.locked:
            raise RuntimeError(
                "Cannot analyze odds with an unlocked model."
            )

        # =================================================
        # SNAPSHOT REFERENCE
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

        fair_odds: Dict[str, float] = {}

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
        #
        # EV = Model Probability × Odds - 1
        # =================================================

        ev: Dict[str, float] = {}

        for (
            outcome,
            price,
        ) in normalized_odds.items():

            probability = (
                self.snapshot.probabilities.get(
                    outcome
                )
            )

            # Odds marketinde model karşılığı
            # bulunmuyorsa hesaplama yapılmaz.
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
            validated_bankroll,
            uncertainty=normalized_uncertainty,
        )

        # =================================================
        # MODEL LOCK INTEGRITY CHECK
        # =================================================

        if self.snapshot is not snapshot_before:
            raise RuntimeError(
                "CRITICAL: model snapshot reference "
                "was replaced during odds analysis."
            )

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

        stats = TeamStats(
            2.0,
            1.2,
            1.5,
            1.8,
            1.1,
            1.0,
            1.4,
        )

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

    pipeline = Q200Pipeline(
        stats
    )

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )
