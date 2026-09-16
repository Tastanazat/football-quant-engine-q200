"""
Q200 Engine - Pipeline

Q200 V3.1

AŞAMA 1:
Statistics -> Lambda -> Model -> Monte Carlo -> LOCK

AŞAMA 2:
Odds -> No-Vig -> Fair Odds -> EV -> Selection -> Kelly

Odds hiçbir şekilde LOCK edilmiş modeli değiştiremez.
"""

from __future__ import annotations

from dataclasses import replace

from .schema import (
    TeamStats,
    ModelSnapshot,
    AnalysisResult,
)
from .model import build_model
from .monte_carlo import simulate_match
from .odds import (
    implied_probabilities,
    fair_odds,
    expected_value,
)
from .selection import select


class Q200Pipeline:

    def __init__(
        self,
        stats: TeamStats,
        max_goals: int = 10,
    ):

        self.stats = stats

        self.snapshot = build_model(
            stats,
            max_goals=max_goals,
        )

        if not self.snapshot.locked:
            raise RuntimeError(
                "Model LOCK edilemedi."
            )

    # =====================================================
    # MODEL
    # =====================================================

    def run_monte_carlo(
        self,
        iterations: int = 100_000,
    ):

        return simulate_match(
            self.snapshot.lambda_home,
            self.snapshot.lambda_away,
            iterations=iterations,
        )

    # =====================================================
    # ODDS ANALYSIS
    # =====================================================

    def analyze_odds(
        self,
        odds: dict[str, float],
        bankroll: float,
        uncertainty: str = "MEDIUM",
    ) -> AnalysisResult:

        # LOCK edilmiş snapshot'ın kopyasını al.
        locked_snapshot = self.snapshot

        # Odds sadece burada kullanılır.
        no_vig = implied_probabilities(
            odds
        )

        fair = fair_odds(
            locked_snapshot.probabilities
        )

        ev = {}

        for outcome, odd in odds.items():

            if outcome in locked_snapshot.probabilities:

                ev[outcome] = expected_value(
                    locked_snapshot.probabilities[outcome],
                    odd,
                )

        selections = select(
            locked_snapshot.probabilities,
            odds,
            bankroll,
            uncertainty=uncertainty,
        )

        # Modelin değişmediğini garanti et.
        if locked_snapshot != self.snapshot:
            raise RuntimeError(
                "CRITICAL: Odds model snapshot'ını değiştirdi."
            )

        return AnalysisResult(
            snapshot=locked_snapshot,
            fair_odds=fair,
            no_vig_probabilities=no_vig,
            ev=ev,
            selections=selections,
        )
