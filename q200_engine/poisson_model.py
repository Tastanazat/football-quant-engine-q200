import math


def poisson_pmf(k: int, lam: float) -> float:
    if lam < 0:
        raise ValueError("lambda must be >= 0")
    return math.exp(-lam) * lam**k / math.factorial(k)


def _score_matrix(lambda_home, lambda_away, max_goals):
    home = [poisson_pmf(i, lambda_home) for i in range(max_goals + 1)]
    away = [poisson_pmf(j, lambda_away) for j in range(max_goals + 1)]
    matrix = [[home[i] * away[j] for j in range(max_goals + 1)]
              for i in range(max_goals + 1)]
    total = sum(map(sum, matrix))
    return [[p / total for p in row] for row in matrix]


def poisson_match_probabilities(lambda_home, lambda_away, max_goals=10):
    if max_goals < 3:
        raise ValueError("max_goals must be >= 3")

    m = _score_matrix(lambda_home, lambda_away, max_goals)
    home = sum(m[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i > j)
    draw = sum(m[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i == j)
    away = sum(m[i][j] for i in range(max_goals + 1) for j in range(max_goals + 1) if i < j)

    return {"HOME": home, "DRAW": draw, "AWAY": away}
