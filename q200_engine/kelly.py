def kelly_fraction(probability, odds):
    b = odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - probability
    return max(0.0, (b * probability - q) / b)


def quarter_kelly(probability, odds, bankroll, max_risk=0.02):
    raw = kelly_fraction(probability, odds)
    fraction = min(raw / 4.0, max_risk)
    return {
        "kelly_fraction": raw,
        "quarter_kelly_fraction": raw / 4.0,
        "risk_fraction": fraction,
        "stake": bankroll * fraction,
    }
