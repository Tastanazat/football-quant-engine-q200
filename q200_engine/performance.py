"""
Q200 Engine - History Performance

Q200 V3.1

History içinde kalıcı olarak saklanan settlement sonuçlarını toplu
performans metriklerine dönüştürür.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection üretmez.
- Settlement verisini değiştirmez.
- Sadece kayıtlı sonuçları ölçer.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


PERFORMANCE_VERSION = "Q200-PERFORMANCE-V1"


@dataclass(frozen=True)
class PerformanceSummary:
    """History settlement kayıtlarının toplu performans özeti."""

    total_analysis_records: int
    completed_matches: int
    settled_matches: int
    unsettled_completed_matches: int

    total_bets: int
    wins: int
    losses: int
    voids: int

    total_stake: float
    total_profit: float
    roi: float
    hit_rate: float

    starting_bankroll: float
    ending_bankroll: float

    @property
    def profit(self) -> float:
        """BacktestSummary ile uyumlu total_profit alias'ı."""

        return self.total_profit


def _validate_bankroll(
    value: Any,
) -> float:

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            "starting_bankroll sayısal olmalıdır."
        )

    try:

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "starting_bankroll sayısal olmalıdır."
        ) from exc

    if not isfinite(
        result
    ):

        raise ValueError(
            "starting_bankroll sonlu bir sayı olmalıdır."
        )

    if result < 0:

        raise ValueError(
            "starting_bankroll negatif olamaz."
        )

    return result


def _validate_history(
    history: Any,
) -> None:

    if history is None:

        raise TypeError(
            "history verilmelidir."
        )

    required_methods = (
        "count",
        "count_completed",
        "list",
        "get",
    )

    for method in required_methods:

        if not callable(
            getattr(
                history,
                method,
                None,
            )
        ):

            raise TypeError(
                "history AnalysisHistory benzeri "
                "bir repository olmalıdır."
            )


def _number(
    value: Any,
    name: str,
) -> float:

    if isinstance(
        value,
        bool,
    ):

        raise TypeError(
            f"{name} sayısal olmalıdır."
        )

    try:

        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            f"{name} sayısal olmalıdır."
        ) from exc

    if not isfinite(
        result
    ):

        raise ValueError(
            f"{name} sonlu bir sayı olmalıdır."
        )

    return result


def summarize_history(
    history,
    *,
    starting_bankroll: float = 0.0,
) -> PerformanceSummary:
    """
    History içindeki settlement sonuçlarını toplu olarak hesaplar.

    Yalnızca settlement_recorded=True olan kayıtların bahis sonuçları
    performans hesabına dahil edilir.
    """

    _validate_history(
        history
    )

    starting_bankroll = _validate_bankroll(
        starting_bankroll
    )

    total_analysis_records = (
        history.count()
    )

    completed_matches = (
        history.count_completed()
    )

    if total_analysis_records > 0:

        records = history.list(
            limit=total_analysis_records
        )

    else:

        records = []

    settled_records = []

    for item in records:

        if item.get(
            "settlement_recorded"
        ) is not True:

            continue

        record = history.get(
            item["id"]
        )

        if record is None:

            continue

        settlement = record.get(
            "settlement"
        )

        if not isinstance(
            settlement,
            dict,
        ):

            raise ValueError(
                "Settlement kaydı dictionary olmalıdır."
            )

        settled_records.append(
            settlement
        )

    settled_matches = len(
        settled_records
    )

    unsettled_completed_matches = (
        completed_matches
        - settled_matches
    )

    if unsettled_completed_matches < 0:

        raise ValueError(
            "Settlement sayısı sonuçlanmış "
            "maç sayısından fazla olamaz."
        )

    total_bets = 0
    wins = 0
    losses = 0
    voids = 0

    total_stake = 0.0
    total_profit = 0.0

    for settlement in settled_records:

        selections = settlement.get(
            "selections"
        )

        if not isinstance(
            selections,
            list,
        ):

            raise ValueError(
                "Settlement selections list olmalıdır."
            )

        for selection in selections:

            if not isinstance(
                selection,
                dict,
            ):

                raise ValueError(
                    "Settlement selection "
                    "dictionary olmalıdır."
                )

            outcome = str(
                selection.get(
                    "settlement",
                    "",
                )
            ).strip().upper()

            if outcome not in {
                "WIN",
                "LOSS",
                "VOID",
            }:

                raise ValueError(
                    "Geçersiz settlement sonucu: "
                    f"{selection.get('settlement')}"
                )

            stake = _number(
                selection.get(
                    "stake"
                ),
                "stake",
            )

            profit = _number(
                selection.get(
                    "profit"
                ),
                "profit",
            )

            if stake < 0:

                raise ValueError(
                    "Settlement stake negatif olamaz."
                )

            total_bets += 1

            total_stake += stake

            total_profit += profit

            if outcome == "WIN":

                wins += 1

            elif outcome == "LOSS":

                losses += 1

            else:

                voids += 1

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

    ending_bankroll = (
        starting_bankroll
        + total_profit
    )

    return PerformanceSummary(
        total_analysis_records=(
            total_analysis_records
        ),
        completed_matches=(
            completed_matches
        ),
        settled_matches=(
            settled_matches
        ),
        unsettled_completed_matches=(
            unsettled_completed_matches
        ),
        total_bets=(
            total_bets
        ),
        wins=(
            wins
        ),
        losses=(
            losses
        ),
        voids=(
            voids
        ),
        total_stake=(
            total_stake
        ),
        total_profit=(
            total_profit
        ),
        roi=(
            roi
        ),
        hit_rate=(
            hit_rate
        ),
        starting_bankroll=(
            starting_bankroll
        ),
        ending_bankroll=(
            ending_bankroll
        ),
    )
