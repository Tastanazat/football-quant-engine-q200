from dataclasses import asdict
from .model import build_model
from .monte_carlo import simulate_match
from .selection import select
from .schema import TeamStats


class Q200Pipeline:
    """Strict two-stage pipeline: model first, odds second."""

    def __init__(self, stats: TeamStats, max_goals=10):
        self.snapshot = build_model(stats, max_goals=max_goals)
        self.monte_carlo = simulate_match(
            self.snapshot.lambda_home,
            self.snapshot.lambda_away,
            iterations=100_000,
        )

    def analyze_odds(self, odds, bankroll, uncertainty="MEDIUM"):
        if not self.snapshot.locked:
            raise RuntimeError("model must be locked before odds analysis")
        selections = select(
            self.snapshot.probabilities,
            odds,
            bankroll,
            uncertainty=uncertainty,
        )
        return {
            "model": asdict(self.snapshot),
            "monte_carlo": self.monte_carlo,
            "selections": selections,
        }
