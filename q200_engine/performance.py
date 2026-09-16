"""
Q200 Engine - History Performance

Q200 V3.1

Kalıcı History kayıtlarındaki settlement sonuçlarını toplu olarak
ölçer.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection üretmez.
- Kayıtlı settlement verisini değiştirmez.
- Sadece gerçekleşmiş performansı özetler.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


PERFORMANCE_VERSION = "Q200-PERFORMANCE-V1"


@dataclass(frozen=True)
class PerformanceSummary:
    """History settlement performansının toplu özeti."""

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
        """Geriye dönük kullanım için total_profit alias'ı."""

        return self.total_profit


def _validate_bankroll(
    value: Any,
) -> float:

    try:
        result = float(value)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            "starting_bankroll sayısal olmalıdır."
        ) from exc

    if not isfinite(result):

        raise ValueError(
            "starting_bankroll sonlu bir sayı olmalıdır."
        )

    if result < 0:

        raise ValueError(
            "starting_bankroll negatif olamaz."
        )

    return result


def _validate_records(
    records: Any,
) -> list[dict[str, Any]]:

    if not isinstance(
        records,
        list,
    ):

        raise TypeError(
            "records list olmalıdır."
        )

    for record in records:

        if not isinstance(
            record,
            dict,
        ):

            raise TypeError(
                "Her history record dictionary olmalıdır."
            )

    return records


def summarize_history(
    history,
    *,
    starting_bankroll: float = 0.0,
) -> PerformanceSummary:
    """
    AnalysisHistory içindeki settlement kayıtlarını özetler.

    Yalnızca settlement_recorded=True olan kayıtların bahis sonuçları
    performans hesabına dahil edilir.
    """

    if history is None:

        raise TypeError(
            "history verilmelidir."
        )

    starting_bankroll = _validate_bankroll(
        starting_bankroll
    )

    total_analysis_records = history.count()

    records = history.list(
        limit=max(
            total_analysis_records,
            1,
        )
    )

    completed_matches = sum(
        1
        for record in records
        if record.get(
            "result_recorded"
        ) is True
    )

    settled_records: list[
        dict[str, Any]
    ] = []

    for record in records:

        if record.get(
            "settlement_recorded"
        ) is not True:

            continue

        full_record = history.get(
            record["id"]
        )

        if full_record is None:

            continue

        settlement = full_record.get(
            "settlement"
        )

        if not isinstance(
            settlement,
            dict,
        ):

            continue

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

    total_bets = 0
    wins = 0
    losses = 0
    voids = 0

    total_stake = 0.0
    total_profit = 0.0

    for settlement in settled_records:

        summary = settlement.get(
            "summary"
        )

        selections = settlement.get(
            "selections",
            [],
        )

        if not isinstance(
            summary,
            dict,
        ):

            raise ValueError(
                "Settlement summary dictionary olmalıdır."
            )

        if not isinstance(
            selections,
            list,
        ):

            raise ValueError(
                "Settlement selections list olmalıdır."
            )

        # Gerçek settlement satırlarını canonical
        # kaynak kabul ediyoruz.
        for selection in selections:

            if not isinstance(
                selection,
                dict,
            ):

                raise ValueError(
                    "Settlement selection dictionary olmalıdır."
                )

            settlement_result = str(
                selection.get(
                    "settlement",
                    "",
                )
            ).strip().upper()

            if settlement_result not in {
                "WIN",
                "LOSS",
                "VOID",
            }:

                raise ValueError(
                    "Geçersiz settlement sonucu: "
                    f"{selection.get('settlement')}"
                )

            try:

                stake = float(
                    selection.get(
                        "stake",
                        0.0,
                    )
                )

                profit = float(
                    selection.get(
                        "profit",
                        0.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "Settlement stake/profit sayısal olmalıdır."
                ) from exc

            if (
                not isfinite(stake)
                or not isfinite(profit)
            ):

                raise ValueError(
                    "Settlement stake/profit sonlu olmalıdır."
                )

            if stake < 0:

                raise ValueError(
                    "Settlement stake negatif olamaz."
                )

            total_bets += 1

            total_stake += stake

            total_profit += profit

            if settlement_result == "WIN":

                wins += 1

            elif settlement_result == "LOSS":

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
