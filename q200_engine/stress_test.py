def stress_probabilities(probabilities, multipliers=None):
    multipliers = multipliers or {
        "OPTIMISTIC": 1.05,
        "BASELINE": 1.00,
        "PESSIMISTIC": 0.95,
    }

    results = {}
    for scenario, multiplier in multipliers.items():
        adjusted = {k: max(0.0, v * multiplier) for k, v in probabilities.items()}
        total = sum(adjusted.values())
        results[scenario] = {k: v / total for k, v in adjusted.items()}
    return results
