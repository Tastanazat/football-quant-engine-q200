from .schema import TeamStats, ModelSnapshot
from .poisson_model import poisson_match_probabilities


MODEL_VERSION = "Q200-V1.0"


def _weighted(values):
    return sum(v * w for v, w in values) / sum(w for _, w in values)


def calculate_lambdas(stats: TeamStats):
    # Fixed Q200 weights. If xG/xGA are unavailable, their 15% weights
    # are redistributed proportionally over the available components.
    home_parts = [(stats.home_gf, 0.35), (stats.away_ga, 0.35)]
    away_parts = [(stats.away_gf, 0.35), (stats.home_ga, 0.35)]

    if stats.home_xg is not None and stats.away_xga is not None:
        home_parts += [(stats.home_xg, 0.15), (stats.away_xga, 0.15)]

    if stats.away_xg is not None and stats.home_xga is not None:
        away_parts += [(stats.away_xg, 0.15), (stats.home_xga, 0.15)]

    return _weighted(home_parts), _weighted(away_parts)


def build_model(stats: TeamStats, max_goals: int = 10) -> ModelSnapshot:
    lh, la = calculate_lambdas(stats)
    probs = poisson_match_probabilities(lh, la, max_goals=max_goals)
    return ModelSnapshot(
        lambda_home=lh,
        lambda_away=la,
        probabilities=probs,
        max_goals=max_goals,
        model_version=MODEL_VERSION,
        locked=True,
    )
