"""
Q200 Engine - Backtest Layer

Q200 V3.1

Geçmiş maçlarda Q200 seçimlerinin sonuçlarını ölçer.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, List


# =========================================================
# VALIDATION
# =========================================================

def _validate_number(
    value: float,
    name: str,
) -> float:

    try:
        result = float(value)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            f"{name} sayısal olmalıdır."
        ) from exc

    if not isfinite(result):

        raise ValueError(
            f"{name} sonlu bir sayı olmalıdır."
        )

    return result


def _validate_goals(
    goals: int,
    name: str,
) -> int:

    if not isinstance(goals, int):

        raise TypeError(
            f"{name} integer olmalıdır."
        )

    if goals < 0:

        raise ValueError(
            f"{name} negatif olamaz."
        )

    return goals


# =========================================================
# SETTLEMENT
# =========================================================

def settle_market(
    outcome: str,
    home_goals: int,
    away_goals: int,
) -> str:

    home_goals = _validate_goals(
        home_goals,
        "home_goals",
    )

    away_goals = _validate_goals(
        away_goals,
        "away_goals",
    )

    market = str(
        outcome
    ).strip().upper()

    # -----------------------------------------------------
    # 1X2
    # -----------------------------------------------------

    if market == "HOME":

        return (
            "WIN"
            if home_goals > away_goals
            else "LOSS"
        )

    if market == "DRAW":

        return (
            "WIN"
            if home_goals == away_goals
            else "LOSS"
        )

    if market == "AWAY":

        return (
            "WIN"
            if away_goals > home_goals
            else "LOSS"
        )

    # -----------------------------------------------------
    # TOTAL GOALS
    # -----------------------------------------------------

    if market.startswith("OVER_"):

        try:

            line = float(
                market.replace(
                    "OVER_",
                    "",
                )
            )

        except ValueError as exc:

            raise ValueError(
                f"Geçersiz market: {outcome}"
            ) from exc

        total_goals = (
            home_goals
            + away_goals
        )

        return (
            "WIN"
            if total_goals > line
            else "LOSS"
        )

    if market.startswith("UNDER_"):

        try:

            line = float(
                market.replace(
                    "UNDER_",
                    "",
                )
            )

        except ValueError as exc:

            raise ValueError(
                f"Geçersiz market: {outcome}"
            ) from exc

        total_goals = (
            home_goals
            + away_goals
        )

        return (
            "WIN"
            if total_goals < line
            else "LOSS"
        )

    # -----------------------------------------------------
    # BTTS
    # -----------------------------------------------------

    if market == "BTTS_YES":

        return (
            "WIN"
            if (
                home_goals >= 1
                and away_goals >= 1
            )
            else "LOSS"
        )

    if market == "BTTS_NO":

        return (
            "WIN"
            if (
                home_goals == 0
                or away_goals == 0
            )
            else "LOSS"
        )

    # -----------------------------------------------------
    # CORRECT SCORE
    # -----------------------------------------------------

    if "-" in market:

        parts = market.split("-")

        if len(parts) != 2:

            raise ValueError(
                "Geçersiz correct score marketi: "
                f"{outcome}"
            )

        try:

            expected_home = int(
                parts[0]
            )

            expected_away = int(
                parts[1]
            )

        except ValueError as exc:

            raise ValueError(
                "Geçersiz correct score marketi: "
                f"{outcome}"
            ) from exc

        if (
            expected_home < 0
            or expected_away < 0
        ):

            raise ValueError(
                "Geçersiz correct score marketi: "
                f"{outcome}"
            )

        return (
            "WIN"
            if (
                home_goals == expected_home
                and away_goals == expected_away
            )
            else "LOSS"
        )

    raise ValueError(
        f"Desteklenmeyen market: {outcome}"
    )


# =========================================================
# PROFIT
# =========================================================

def calculate_profit(
    settlement: str,
    stake: float,
    odds: float,
) -> float:

    stake = _validate_number(
        stake,
        "stake",
    )

    odds = _validate_number(
        odds,
        "odds",
    )

    if stake < 0:

        raise ValueError(
            "stake negatif olamaz."
        )

    if odds <= 1.0:

        raise ValueError(
            "odds 1'den büyük olmalıdır."
        )

    result = str(
        settlement
    ).strip().upper()

    if result == "WIN":

        return stake * (
            odds - 1.0
        )

    if result == "LOSS":

        return -stake

    if result == "VOID":

        return 0.0

    raise ValueError(
        f"Geçersiz settlement: {settlement}"
    )


# =========================================================
# BACKTEST RECORD
# =========================================================

@dataclass(frozen=True)
class BacktestRecord:

    outcome: str
    odds: float
    stake: float
    settlement: str
    profit: float

    home_goals: int
    away_goals: int


# =========================================================
# SINGLE BET
# =========================================================

def settle_bet(
    outcome: str,
    odds: float,
    stake: float,
    home_goals: int,
    away_goals: int,
) -> BacktestRecord:

    odds = _validate_number(
        odds,
        "odds",
    )

    stake = _validate_number(
        stake,
        "stake",
    )

    if odds <= 1.0:

        raise ValueError(
            "odds 1'den büyük olmalıdır."
        )

    if stake < 0:

        raise ValueError(
            "stake negatif olamaz."
        )

    home_goals = _validate_goals(
        home_goals,
        "home_goals",
    )

    away_goals = _validate_goals(
        away_goals,
        "away_goals",
    )

    settlement = settle_market(
        outcome,
        home_goals,
        away_goals,
    )

    profit = calculate_profit(
        settlement,
        stake,
        odds,
    )

    return BacktestRecord(
        outcome=str(
            outcome
        ).upper(),
        odds=odds,
        stake=stake,
        settlement=settlement,
        profit=profit,
        home_goals=home_goals,
        away_goals=away_goals,
    )


# =========================================================
# BACKTEST SUMMARY
# =========================================================

@dataclass(frozen=True)
class BacktestSummary:

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
        """
        Geriye dönük uyumluluk.

        Eski kullanım:
            summary.profit

        Yeni canonical alan:
            summary.total_profit
        """

        return self.total_profit


# =========================================================
# BACKTEST ENGINE
# =========================================================

class BacktestEngine:

    def __init__(
        self,
        starting_bankroll: float = 0.0,
    ) -> None:

        starting_bankroll = _validate_number(
            starting_bankroll,
            "starting_bankroll",
        )

        if starting_bankroll < 0:

            raise ValueError(
                "starting_bankroll negatif olamaz."
            )

        self.starting_bankroll = (
            starting_bankroll
        )

        self.records: List[
            BacktestRecord
        ] = []


    # =====================================================
    # ADD BET
    # =====================================================

    def add_bet(
        self,
        outcome: str,
        odds: float,
        stake: float,
        home_goals: int,
        away_goals: int,
    ) -> BacktestRecord:

        record = settle_bet(
            outcome=outcome,
            odds=odds,
            stake=stake,
            home_goals=home_goals,
            away_goals=away_goals,
        )

        self.records.append(
            record
        )

        return record


    # =====================================================
    # ADD SELECTION
    # =====================================================

    def add_selection(
        self,
        selection: dict,
        home_goals: int,
        away_goals: int,
    ) -> BacktestRecord | None:

        if not isinstance(
            selection,
            dict,
        ):

            raise TypeError(
                "selection dictionary olmalıdır."
            )

        eligible = bool(
            selection.get(
                "eligible",
                False,
            )
        )

        if not eligible:

            return None

        if "outcome" not in selection:

            raise ValueError(
                "selection outcome içermelidir."
            )

        if "odds" not in selection:

            raise ValueError(
                "selection odds içermelidir."
            )

        if "stake" not in selection:

            raise ValueError(
                "selection stake içermelidir."
            )

        return self.add_bet(
            outcome=selection["outcome"],
            odds=selection["odds"],
            stake=selection["stake"],
            home_goals=home_goals,
            away_goals=away_goals,
        )


    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self) -> BacktestSummary:

        total_bets = len(
            self.records
        )

        wins = sum(
            1
            for record in self.records
            if record.settlement == "WIN"
        )

        losses = sum(
            1
            for record in self.records
            if record.settlement == "LOSS"
        )

        voids = sum(
            1
            for record in self.records
            if record.settlement == "VOID"
        )

        total_stake = sum(
            record.stake
            for record in self.records
        )

        total_profit = sum(
            record.profit
            for record in self.records
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

        ending_bankroll = (
            self.starting_bankroll
            + total_profit
        )

        return BacktestSummary(
            total_bets=total_bets,
            wins=wins,
            losses=losses,
            voids=voids,
            total_stake=total_stake,
            total_profit=total_profit,
            roi=roi,
            hit_rate=hit_rate,
            starting_bankroll=(
                self.starting_bankroll
            ),
            ending_bankroll=(
                ending_bankroll
            ),
        )


# =========================================================
# BATCH BACKTEST
# =========================================================

def run_backtest(
    selections: Iterable[dict],
    home_goals: int | None = None,
    away_goals: int | None = None,
    starting_bankroll: float = 0.0,
) -> BacktestSummary:
    """
    Birden fazla seçimi backtest eder.

    İki kullanım desteklenir.

    ---------------------------------------------------------
    1. Ortak maç skoru
    ---------------------------------------------------------

    run_backtest(
        selections,
        home_goals=2,
        away_goals=1,
    )

    Bu kullanımda tüm selections aynı maç skoruyla
    settle edilir.

    ---------------------------------------------------------
    2. Her selection kendi maç skorunu taşır
    ---------------------------------------------------------

    run_backtest(
        [
            {
                "outcome": "HOME",
                "odds": 2.00,
                "stake": 100,
                "home_goals": 2,
                "away_goals": 1,
                "eligible": True,
            }
        ]
    )

    Bu kullanımda her selection içindeki
    home_goals / away_goals kullanılır.

    Böylece eski ve yeni API birlikte korunur.
    """

    if home_goals is not None:

        home_goals = _validate_goals(
            home_goals,
            "home_goals",
        )

    if away_goals is not None:

        away_goals = _validate_goals(
            away_goals,
            "away_goals",
        )

    if (
        (home_goals is None)
        != (away_goals is None)
    ):

        raise ValueError(
            "home_goals ve away_goals "
            "birlikte verilmelidir."
        )

    engine = BacktestEngine(
        starting_bankroll=starting_bankroll,
    )

    for selection in selections:

        if not isinstance(
            selection,
            dict,
        ):

            raise TypeError(
                "selection dictionary olmalıdır."
            )

        # -------------------------------------------------
        # Ortak maç skoru verilmişse onu kullan.
        # -------------------------------------------------

        if (
            home_goals is not None
            and away_goals is not None
        ):

            match_home_goals = (
                home_goals
            )

            match_away_goals = (
                away_goals
            )

        # -------------------------------------------------
        # Ortak skor yoksa selection içinden al.
        # -------------------------------------------------

        else:

            if (
                "home_goals" not in selection
                or "away_goals" not in selection
            ):

                raise ValueError(
                    "Ortak maç skoru verilmediğinde "
                    "her selection home_goals ve "
                    "away_goals içermelidir."
                )

            match_home_goals = (
                selection["home_goals"]
            )

            match_away_goals = (
                selection["away_goals"]
            )

        engine.add_selection(
            selection,
            match_home_goals,
            match_away_goals,
        )

    return engine.summary()
