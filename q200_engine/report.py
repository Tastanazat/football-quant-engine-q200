"""
Q200 Engine - Reporting Layer

Q200 V3.1

AnalysisResult nesnesini standart, okunabilir ve JSON'a uygun
Q200 raporuna dönüştürür.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection değiştirmez.
- Stake değiştirmez.
- AnalysisResult üzerinde mutation yapmaz.
"""

from __future__ import annotations

import json
import math
from typing import Any

from .schema import AnalysisResult


REPORT_VERSION = "Q200-REPORT-V1"


def _json_safe(value: Any) -> Any:
    """Değerleri JSON-safe hale getirir; hesapları değiştirmez."""

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(value, float):
        if math.isnan(value):
            return None

        if math.isinf(value):
            return (
                "Infinity"
                if value > 0
                else "-Infinity"
            )

    return value


def build_report(
    result: AnalysisResult,
) -> dict[str, Any]:
    """
    AnalysisResult'tan standart Q200 raporu üretir.
    """

    if not isinstance(
        result,
        AnalysisResult,
    ):
        raise TypeError(
            "result AnalysisResult olmalıdır."
        )

    snapshot = result.snapshot

    eligible_selections = [
        selection
        for selection in result.selections
        if selection.get("eligible") is True
    ]

    total_stake = sum(
        float(
            selection.get(
                "stake",
                0.0,
            )
        )
        for selection in eligible_selections
    )

    return _json_safe(
        {
            "report_version": REPORT_VERSION,
            "model_version": snapshot.model_version,
            "model_locked": snapshot.locked,

            "model": {
                "lambda_home": snapshot.lambda_home,
                "lambda_away": snapshot.lambda_away,

                "probabilities": dict(
                    snapshot.probabilities
                ),

                "monte_carlo_probabilities": dict(
                    snapshot.monte_carlo_probabilities
                ),

                "max_goals": snapshot.max_goals,
            },

            "stress_test": {
                "lambdas": dict(
                    result.stress_lambdas
                ),

                "probabilities": dict(
                    result.stress_probabilities
                ),
            },

            "odds_analysis": {
                "fair_odds": dict(
                    result.fair_odds
                ),

                "no_vig_probabilities": dict(
                    result.no_vig_probabilities
                ),

                "baseline_ev": dict(
                    result.ev
                ),

                "pessimistic_probabilities": dict(
                    result.pessimistic_probabilities
                ),

                "pessimistic_ev": dict(
                    result.pessimistic_ev
                ),
            },

            "selection": {
                "selections": list(
                    result.selections
                ),

                "eligible_count": len(
                    eligible_selections
                ),

                "total_stake": total_stake,
            },
        }
    )


def report_to_json(
    result: AnalysisResult,
    *,
    indent: int = 2,
) -> str:
    """
    AnalysisResult'ı standart JSON raporuna dönüştürür.
    """

    if not isinstance(
        indent,
        int,
    ):
        raise TypeError(
            "indent integer olmalıdır."
        )

    if indent < 0:
        raise ValueError(
            "indent negatif olamaz."
        )

    return json.dumps(
        build_report(result),
        ensure_ascii=False,
        indent=indent,
        sort_keys=False,
    )


def report_to_text(
    result: AnalysisResult,
) -> str:
    """
    AnalysisResult'ı kullanıcı tarafından okunabilir
    kısa Q200 raporuna dönüştürür.
    """

    if not isinstance(
        result,
        AnalysisResult,
    ):
        raise TypeError(
            "result AnalysisResult olmalıdır."
        )

    snapshot = result.snapshot

    lines = [
        "Q200 V3.1 ANALİZ RAPORU",
        "=" * 30,

        f"Model Version : {snapshot.model_version}",
        f"Model Locked  : {snapshot.locked}",

        "",

        "MODEL",

        f"Lambda Home   : "
        f"{snapshot.lambda_home:.6f}",

        f"Lambda Away   : "
        f"{snapshot.lambda_away:.6f}",

        "",

        "MODEL PROBABILITIES",
    ]

    for outcome, probability in (
        snapshot.probabilities.items()
    ):
        lines.append(
            f"{outcome:<8}: "
            f"{probability:.2%}"
        )

    if snapshot.monte_carlo_probabilities:

        lines.extend(
            [
                "",
                "MONTE CARLO",
            ]
        )

        for (
            outcome,
            probability,
        ) in snapshot.monte_carlo_probabilities.items():

            lines.append(
                f"{outcome:<8}: "
                f"{probability:.2%}"
            )

    lines.extend(
        [
            "",
            "ODDS ANALYSIS",
        ]
    )

    for (
        outcome,
        probability,
    ) in result.no_vig_probabilities.items():

        fair = result.fair_odds.get(
            outcome
        )

        ev = result.ev.get(
            outcome
        )

        fair_text = (
            f"{fair:.3f}"
            if isinstance(
                fair,
                (int, float),
            )
            and math.isfinite(
                float(fair)
            )
            else "Infinity"
        )

        ev_text = (
            f"{ev:+.2%}"
            if isinstance(
                ev,
                (int, float),
            )
            else "N/A"
        )

        lines.append(
            f"{outcome:<8}: "
            f"No-Vig {probability:.2%} | "
            f"Fair {fair_text} | "
            f"EV {ev_text}"
        )

    lines.extend(
        [
            "",
            "PESSIMISTIC EV",
        ]
    )

    for outcome, ev in (
        result.pessimistic_ev.items()
    ):
        lines.append(
            f"{outcome:<8}: "
            f"{ev:+.2%}"
        )

    lines.extend(
        [
            "",
            "SELECTION",
        ]
    )

    if not result.selections:
        lines.append(
            "No selection"
        )

    else:

        for selection in (
            result.selections
        ):
            outcome = selection.get(
                "outcome",
                "?",
            )

            eligible = selection.get(
                "eligible",
                False,
            )

            odds = selection.get(
                "odds",
                "N/A",
            )

            stake = selection.get(
                "stake",
                0.0,
            )

            reason = selection.get(
                "reason",
                "",
            )

            lines.append(
                f"{outcome:<8}: "
                f"eligible={eligible} | "
                f"odds={odds} | "
                f"stake={stake:.2f} | "
                f"{reason}"
            )

    total_stake = sum(
        float(
            selection.get(
                "stake",
                0.0,
            )
        )
        for selection in result.selections
        if selection.get(
            "eligible"
        ) is True
    )

    eligible_count = sum(
        1
        for selection in result.selections
        if selection.get(
            "eligible"
        ) is True
    )

    lines.extend(
        [
            "",
            f"Eligible Selections : "
            f"{eligible_count}",

            f"Total Eligible Stake: "
            f"{total_stake:.2f}",
        ]
    )

    return "\n".join(lines)
