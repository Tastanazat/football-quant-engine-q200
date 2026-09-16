def validate_odds(odds, minimum=1.50):
    if not odds:
        raise ValueError("odds cannot be empty")
    for outcome, odd in odds.items():
        if odd <= 1:
            raise ValueError(f"invalid odds for {outcome}: {odd}")
        if odd < minimum:
            raise ValueError(f"odds below Q200 minimum ({minimum}): {outcome}={odd}")


def implied_probabilities(odds):
    validate_odds(odds, minimum=1.01)
    raw = {k: 1.0 / v for k, v in odds.items()}
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def fair_odds(probabilities):
    return {k: 1.0 / p for k, p in probabilities.items() if p > 0}
