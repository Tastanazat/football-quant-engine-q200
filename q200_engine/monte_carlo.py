import random


def simulate_match(lambda_home, lambda_away, iterations=100_000, seed=200):
    if iterations < 100_000:
        raise ValueError("Q200 requires at least 100,000 Monte Carlo iterations")

    rng = random.Random(seed)

    def poisson_sample(lam):
        # Knuth sampler; sufficient for the compact Q200 engine.
        l = pow(2.718281828459045, -lam)
        k, p = 0, 1.0
        while p > l:
            k += 1
            p *= rng.random()
        return k - 1

    h = d = a = 0
    for _ in range(iterations):
        hg = poisson_sample(lambda_home)
        ag = poisson_sample(lambda_away)
        if hg > ag:
            h += 1
        elif hg == ag:
            d += 1
        else:
            a += 1

    return {
        "HOME": h / iterations,
        "DRAW": d / iterations,
        "AWAY": a / iterations,
        "iterations": iterations,
        "seed": seed,
    }
