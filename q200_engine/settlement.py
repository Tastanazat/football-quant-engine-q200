"""
Q200 Engine - Analysis Settlement

Q200 V3.1

Kayıtlı Q200 analizindeki eligible seçimleri,
maçın gerçekleşen skoruyla settle eder.

Bu katman:
- Model hesabı yapmaz.
- Model olasılıklarını değiştirmez.
- Odds değiştirmez.
- Selection üretmez.
- Sadece gerçekleşen sonuç ile kayıtlı seçimleri eşleştirir.
"""

from __future__ import annotations

from typing import Any

from .backtest import settle_bet


SETTLEMENT_VERSION = "Q200-SETTLEMENT-V1"


def _validate_goals(
    value: Any,
    name: str,
) -> int:

    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        int,
    ):
        raise TypeError(
            f"{name} integer olmalıdır."
        )

    if value < 0:
        raise ValueError(
            f"{name} negatif olamaz."
        )

    return value


def settle_analysis_record(
    record: dict[str, Any],
    home_goals: int,
    away_goals: int,
) -> dict[str, Any]:
    """
    History.get() tarafından döndürülen bir analiz kaydını settle eder.

    Yalnızca eligible=True seçimleri settle edilir.
    """

    if not isinstance(
        record,
        dict,
    ):
        raise TypeError(
            "record dictionary olmalıdır."
        )

    if "id" not in record:
        raise ValueError(
            "record id içermelidir."
        )

    if "match_id" not in record:
        raise ValueError(
            "record match_id içermelidir."
        )

    report = record.get(
        "report"
    )

    if not isinstance(
        report,
        dict,
    ):
        raise ValueError(
            "record report dictionary olmalıdır."
        )

    selection_section = report.get(
        "selection"
    )

    if not isinstance(
        selection_section,
        dict,
    ):
        raise ValueError(
            "report selection dictionary içermelidir."
        )

    selections = selection_section.get(
        "selections",
        [],
    )

    if not isinstance(
        selections,
        list,
    ):
        raise ValueError(
            "report selections list olmalıdır."
        )

    home_goals = _validate_goals(
        home_goals,
        "home_goals",
    )

    away_goals = _validate_goals(
        away_goals,
        "away_goals",
    )

    settled = []

    for selection in selections:

        if not isinstance(
            selection,
            dict,
        ):
            raise ValueError(
                "Her selection dictionary olmalıdır."
            )

        if selection.get(
            "eligible"
        ) is not True:
            continue

        required = (
            "outcome",
            "odds",
            "stake",
        )

        missing = [
            field
            for field in required
            if field not in selection
        ]

        if missing:
            raise ValueError(
                "Eligible selection eksik alan içeriyor: "
                + ", ".join(missing)
            )

        result = settle_bet(
            outcome=selection[
                "outcome"
            ],
            odds=selection[
                "odds"
            ],
            stake=selection[
                "stake"
            ],
            home_goals=home_goals,
            away_goals=away_goals,
        )

        settled.append(
            {
                "outcome": result.outcome,
                "odds": result.odds,
                "stake": result.stake,
                "settlement": result.settlement,
                "profit": result.profit,
                "home_goals": result.home_goals,
                "away_goals": result.away_goals,
            }
        )

    total_stake = sum(
        item["stake"]
        for item in settled
    )

    total_profit = sum(
        item["profit"]
        for item in settled
    )

    wins = sum(
        1
        for item in settled
        if item["settlement"] == "WIN"
    )

    losses = sum(
        1
        for item in settled
        if item["settlement"] == "LOSS"
    )

    voids = sum(
        1
        for item in settled
        if item["settlement"] == "VOID"
    )

    if total_stake > 0:

        roi = (
            total_profit
            / total_stake
        )

    else:

        roi = 0.0

    settled_bets = (
        wins
        + losses
    )

    if settled_bets > 0:

        hit_rate = (
            wins
            / settled_bets
        )

    else:

        hit_rate = 0.0

    return {
        "settlement_version": (
            SETTLEMENT_VERSION
        ),

        "record_id": record[
            "id"
        ],

        "match_id": record[
            "match_id"
        ],

        "home_goals": home_goals,

        "away_goals": away_goals,

        "selections": settled,

        "summary": {
            "total_bets": len(
                settled
            ),

            "wins": wins,

            "losses": losses,

            "voids": voids,

            "total_stake": (
                total_stake
            ),

            "total_profit": (
                total_profit
            ),

            "roi": roi,

            "hit_rate": hit_rate,
        },
    }
