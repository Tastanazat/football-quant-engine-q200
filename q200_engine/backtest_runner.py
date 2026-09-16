"""
Q200 Engine - Backtest Runner

Q200 V3.1

History üzerinde kayıtlı analizlerin gerçek maç sonuçlarıyla sırayla
sonuçlandırılmasını ve settlement edilmesini yöneten orchestration katmanıdır.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection değiştirmez.
- Yeni bahis üretmez.
- Backtest matematiğini tekrar etmez.
- History.record_result() ve History.settle_record() kullanır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


BACKTEST_RUNNER_VERSION = "Q200-BACKTEST-RUNNER-V1"


@dataclass(frozen=True)
class BacktestRunItem:
    """Tek bir History kaydının backtest sonucu."""

    record_id: int
    home_goals: int
    away_goals: int
    settlement_recorded: bool
    total_bets: int
    wins: int
    losses: int
    voids: int
    total_stake: float
    total_profit: float


@dataclass(frozen=True)
class BacktestRunSummary:
    """Toplu History backtest çalışmasının özeti."""

    requested_records: int
    processed_records: int
    skipped_records: int
    failed_records: int
    total_bets: int
    wins: int
    losses: int
    voids: int
    total_stake: float
    total_profit: float
    results: tuple[BacktestRunItem, ...]


class BacktestRunner:
    """History sonuçlarını settlement zincirinden geçirir."""

    def __init__(
        self,
        history,
    ) -> None:

        self._validate_history(history)
        self.history = history

    @staticmethod
    def _validate_history(history: Any) -> None:

        if history is None:
            raise TypeError(
                "history verilmelidir."
            )

        required_methods = (
            "get",
            "record_result",
            "settle_record",
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

    @staticmethod
    def _validate_record_id(
        value: Any,
    ) -> int:

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                int,
            )
        ):

            raise TypeError(
                "record_id integer olmalıdır."
            )

        if value <= 0:

            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        return value

    @staticmethod
    def _validate_goals(
        value: Any,
        name: str,
    ) -> int:

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                int,
            )
        ):

            raise TypeError(
                f"{name} integer olmalıdır."
            )

        if value < 0:

            raise ValueError(
                f"{name} negatif olamaz."
            )

        return value

    @staticmethod
    def _validate_item(
        item: Any,
    ) -> tuple[int, int, int]:

        if not isinstance(
            item,
            dict,
        ):

            raise TypeError(
                "Her backtest item dictionary olmalıdır."
            )

        required = (
            "record_id",
            "home_goals",
            "away_goals",
        )

        missing = [
            field
            for field in required
            if field not in item
        ]

        if missing:

            raise ValueError(
                "Backtest item eksik alan içeriyor: "
                + ", ".join(missing)
            )

        record_id = (
            BacktestRunner
            ._validate_record_id(
                item["record_id"]
            )
        )

        home_goals = (
            BacktestRunner
            ._validate_goals(
                item["home_goals"],
                "home_goals",
            )
        )

        away_goals = (
            BacktestRunner
            ._validate_goals(
                item["away_goals"],
                "away_goals",
            )
        )

        return (
            record_id,
            home_goals,
            away_goals,
        )

    def run_one(
        self,
        record_id: int,
        home_goals: int,
        away_goals: int,
    ) -> BacktestRunItem:
        """Tek bir History kaydını sonuçlandırır ve settle eder."""

        record_id = (
            self._validate_record_id(
                record_id
            )
        )

        home_goals = (
            self._validate_goals(
                home_goals,
                "home_goals",
            )
        )

        away_goals = (
            self._validate_goals(
                away_goals,
                "away_goals",
            )
        )

        record = self.history.get(
            record_id
        )

        if record is None:

            raise ValueError(
                f"History kaydı bulunamadı: {record_id}"
            )

        self.history.record_result(
            record_id,
            home_goals,
            away_goals,
        )

        settlement = (
            self.history.settle_record(
                record_id
            )
        )

        summary = settlement.get(
            "summary"
        )

        if not isinstance(
            summary,
            dict,
        ):

            raise ValueError(
                "Settlement summary dictionary olmalıdır."
            )

        return BacktestRunItem(
            record_id=record_id,
            home_goals=home_goals,
            away_goals=away_goals,
            settlement_recorded=True,
            total_bets=int(
                summary.get(
                    "total_bets",
                    0,
                )
            ),
            wins=int(
                summary.get(
                    "wins",
                    0,
                )
            ),
            losses=int(
                summary.get(
                    "losses",
                    0,
                )
            ),
            voids=int(
                summary.get(
                    "voids",
                    0,
                )
            ),
            total_stake=float(
                summary.get(
                    "total_stake",
                    0.0,
                )
            ),
            total_profit=float(
                summary.get(
                    "total_profit",
                    0.0,
                )
            ),
        )

    def run(
        self,
        results: Iterable[
            dict[str, Any]
        ],
        *,
        continue_on_error: bool = False,
    ) -> BacktestRunSummary:
        """
        Bir sonuç listesini sırayla
        History → Result → Settlement
        zincirinden geçirir.
        """

        if isinstance(
            results,
            (
                str,
                bytes,
                dict,
            ),
        ):

            raise TypeError(
                "results iterable dictionary "
                "kayıtlarından oluşmalıdır."
            )

        if not isinstance(
            continue_on_error,
            bool,
        ):

            raise TypeError(
                "continue_on_error boolean olmalıdır."
            )

        items = list(
            results
        )

        output: list[
            BacktestRunItem
        ] = []

        failed_records = 0
        skipped_records = 0

        for item in items:

            try:

                (
                    record_id,
                    home_goals,
                    away_goals,
                ) = self._validate_item(
                    item
                )

                result = self.run_one(
                    record_id,
                    home_goals,
                    away_goals,
                )

                output.append(
                    result
                )

            except (
                TypeError,
                ValueError,
            ):

                failed_records += 1

                if not continue_on_error:
                    raise

        total_bets = sum(
            item.total_bets
            for item in output
        )

        wins = sum(
            item.wins
            for item in output
        )

        losses = sum(
            item.losses
            for item in output
        )

        voids = sum(
            item.voids
            for item in output
        )

        total_stake = sum(
            item.total_stake
            for item in output
        )

        total_profit = sum(
            item.total_profit
            for item in output
        )

        return BacktestRunSummary(
            requested_records=len(
                items
            ),
            processed_records=len(
                output
            ),
            skipped_records=(
                skipped_records
            ),
            failed_records=(
                failed_records
            ),
            total_bets=total_bets,
            wins=wins,
            losses=losses,
            voids=voids,
            total_stake=total_stake,
            total_profit=total_profit,
            results=tuple(
                output
            ),
        )


def run_history_backtest(
    history,
    results: Iterable[
        dict[str, Any]
    ],
    *,
    continue_on_error: bool = False,
) -> BacktestRunSummary:
    """Kısa kullanım için BacktestRunner wrapper'ı."""

    return BacktestRunner(
        history
    ).run(
        results,
        continue_on_error=continue_on_error,
    )
