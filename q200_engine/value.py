def expected_value(probability, odds):
    return probability * odds - 1.0


def ev_table(model_probabilities, odds):
    return {
        outcome: expected_value(model_probabilities[outcome], odd)
        for outcome, odd in odds.items()
        if outcome in model_probabilities
    }


def uncertainty_threshold(level):
    return {
        "LOW": 0.05,
        "MEDIUM": 0.08,
        "HIGH": 0.12,
        "VERY_HIGH": float("inf"),
    }[level.upper()]
