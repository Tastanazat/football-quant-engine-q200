"""
Q200 Engine - Pipeline Layer

Q200 V3.1

Akış:

STATISTICS
    ↓
MODEL
    ↓
LAMBDA
    ↓
POISSON
    ↓
MONTE CARLO
    ↓
MODEL LOCK
    ↓
STRESS TEST
    ↓
ODDS
    ↓
NO-VIG
    ↓
FAIR ODDS
    ↓
BASELINE EV
    ↓
PESSIMISTIC EV
    ↓
SELECTION
    ↓
KELLY

KRİTİK KURAL:

Odds modeli değiştiremez.

Model önce oluşturulur ve LOCK edilir.
Stress Test model Lambda değerlerinden bağımsız
senaryolar üretir.

Selection yalnızca Odds dosyasında bulunan
marketleri değerlendirebilir.
"""

from __future__ import annotations

from .schema import (
    AnalysisResult,
    ModelSnapshot,
    TeamStats,
)

from .model import build_model

from .odds import implied_probabilities

from .selection import select

from .stress_test import (
    stress_lambdas,
    stress_market_probabilities,
)


# =========================================================
# PIPELINE
# =========================================================

class Q200Pipeline:
    """
    Q200 V3.1 ana pipeline.

    Model oluşturulduktan sonra snapshot LOCK edilir.

    Odds ve stress sonuçları ModelSnapshot'ı değiştiremez.
    """

    VERSION = "Q200-V3.1"

    # -----------------------------------------------------
    # INIT
    # -----------------------------------------------------

    def __init__(
        self,
        stats: TeamStats,
    ) -> None:

        if not isinstance(stats, TeamStats):
            raise TypeError(
                "stats TeamStats olmalıdır."
            )

        # -------------------------------------------------
        # MODEL
        # -------------------------------------------------

        self.snapshot: ModelSnapshot = build_model(
            stats
        )

        # -------------------------------------------------
        # MODEL LOCK
        # -------------------------------------------------

        if not self.snapshot.locked:
            raise RuntimeError(
                "Model LOCK edilmeden pipeline devam edemez."
            )

    # =====================================================
    # PROPERTIES
    # =====================================================

    @property
    def model_locked(self) -> bool:
        """
        Model LOCK durumunu döndürür.
        """

        return self.snapshot.locked

    # -----------------------------------------------------

    @property
    def lambda_home(self) -> float:
        """
        LOCK edilmiş HOME lambda.
        """

        return self.snapshot.lambda_home

    # -----------------------------------------------------

    @property
    def lambda_away(self) -> float:
        """
        LOCK edilmiş AWAY lambda.
        """

        return self.snapshot.lambda_away

    # -----------------------------------------------------

    @property
    def probabilities(self) -> dict[str, float]:
        """
        LOCK edilmiş baseline model olasılıklarını döndürür.
        """

        return dict(
            self.snapshot.probabilities
        )

    # =====================================================
    # STRESS TEST
    # =====================================================

    def stress_test(
        self,
        max_goals: int | None = None,
    ) -> dict[str, dict]:
        """
        LOCK edilmiş lambda değerlerinden stress
        senaryolarını üretir.

        Odds kullanılmaz.

        Returns:

            {
                "lambdas": {
                    "OPTIMISTIC": {...},
                    "BASELINE": {...},
                    "PESSIMISTIC": {...},
                },
                "probabilities": {
                    "OPTIMISTIC": {...},
                    "BASELINE": {...},
                    "PESSIMISTIC": {...},
                }
            }
        """

        if max_goals is None:
            max_goals = self.snapshot.max_goals

        lambdas = stress_lambdas(
            self.snapshot.lambda_home,
            self.snapshot.lambda_away,
        )

        probabilities = stress_market_probabilities(
            self.snapshot.lambda_home,
            self.snapshot.lambda_away,
            max_goals=max_goals,
        )

        return {
            "lambdas": lambdas,
            "probabilities": probabilities,
        }

    # =====================================================
    # ODDS ANALYSIS
    # =====================================================

    def analyze_odds(
        self,
        odds: dict[str, float],
        bankroll: float,
        uncertainty: str = "MEDIUM",
    ) -> AnalysisResult:
        """
        LOCK edilmiş model üzerine odds analizi yapar.

        Baseline model:

            Fair Odds
            No-Vig
            Baseline EV

        Pessimistic stress:

            Pessimistic Probability
            Pessimistic EV
            Selection
            Kelly

        ÖNEMLİ:

            Odds modeli değiştiremez.

        Ayrıca Selection yalnızca Odds içinde
        bulunan marketleri değerlendirir.
        """

        # =================================================
        # INPUT VALIDATION
        # =================================================

        if not isinstance(odds, dict):
            raise TypeError(
                "odds dictionary olmalıdır."
            )

        if not odds:
            raise ValueError(
                "odds boş olamaz."
            )

        try:
            validated_bankroll = float(
                bankroll
            )
        except (TypeError, ValueError):
            raise ValueError(
                "bankroll sayısal olmalıdır."
            )

        if validated_bankroll <= 0:
            raise ValueError(
                "bankroll pozitif olmalıdır."
            )

        # =================================================
        # NORMALIZE ODDS
        # =================================================

        normalized_odds: dict[str, float] = {}

        for outcome, odd in odds.items():

            key = str(outcome).upper()

            try:
                value = float(odd)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Geçersiz odds: {outcome}={odd}"
                )

            if value <= 1.0:
                raise ValueError(
                    f"Odds 1.0'dan büyük olmalıdır: {outcome}"
                )

            normalized_odds[key] = value

        # =================================================
        # SNAPSHOT PROTECTION
        # =================================================

        snapshot_before = self.snapshot

        # =================================================
        # BASELINE MODEL
        # =================================================

        baseline_probabilities = dict(
            self.snapshot.probabilities
        )

        # =================================================
        # NO-VIG
        # =================================================

        no_vig = implied_probabilities(
            normalized_odds
        )

        # =================================================
        # BASELINE FAIR ODDS
        # =================================================

        fair_odds: dict[str, float] = {}

        for outcome, probability in (
            baseline_probabilities.items()
        ):

            if probability <= 0:
                continue

            fair_odds[outcome] = (
                1.0 / probability
            )

        # =================================================
        # BASELINE EV
        # =================================================

        baseline_ev: dict[str, float] = {}

        for outcome, odd in (
            normalized_odds.items()
        ):

            if outcome not in baseline_probabilities:
                continue

            baseline_ev[outcome] = (
                baseline_probabilities[outcome]
                * odd
                - 1.0
            )

        # =================================================
        # STRESS TEST
        # =================================================

        stress = self.stress_test()

        stress_lambdas_result = stress[
            "lambdas"
        ]

        stress_probabilities_result = stress[
            "probabilities"
        ]

        # =================================================
        # PESSIMISTIC PROBABILITIES
        # =================================================

        pessimistic_probabilities = dict(
            stress_probabilities_result[
                "PESSIMISTIC"
            ]
        )

        # =================================================
        # ODDS / MARKET MATCH
        # =================================================
        #
        # Stress Test bütün marketleri üretir.
        #
        # Örneğin:
        #
        # HOME
        # DRAW
        # AWAY
        # OVER_0.5
        # UNDER_0.5
        # ...
        # BTTS_YES
        # BTTS_NO
        #
        # Ancak Selection yalnızca Odds dosyasında
        # bulunan marketleri değerlendirmelidir.
        #
        # Böylece:
        #
        # 1X2 odds      -> 3 selection
        # 1X2 + BTTS    -> ilgili marketler
        # vb.
        #
        # Odds modeli değiştirmez.
        # Sadece hangi marketlerin analiz edileceğini belirler.
        # =================================================

        selection_probabilities = {
            outcome: pessimistic_probabilities[outcome]
            for outcome in normalized_odds
            if outcome in pessimistic_probabilities
        }

        # =================================================
        # PESSIMISTIC EV
        # =================================================

        pessimistic_ev: dict[str, float] = {}

        for outcome, odd in (
            normalized_odds.items()
        ):

            if outcome not in pessimistic_probabilities:
                continue

            pessimistic_ev[outcome] = (
                pessimistic_probabilities[outcome]
                * odd
                - 1.0
            )

        # =================================================
        # SELECTION
        # =================================================
        #
        # Q200 V3.1:
        #
        # Selection değerlendirmesinde PESSIMISTIC
        # probability kullanılır.
        #
        # Ancak sadece Odds dosyasında bulunan
        # marketler Selection'a gönderilir.
        #
        # Böylece stress katmanı bütün marketleri
        # üretebilirken selection katmanı yalnızca
        # gerçek odds bulunan marketleri değerlendirir.
        # =================================================

        selections = select(
            selection_probabilities,
            normalized_odds,
            validated_bankroll,
            uncertainty=uncertainty,
        )

        # =================================================
        # MODEL INTEGRITY CHECK
        # =================================================

        if self.snapshot != snapshot_before:
            raise RuntimeError(
                "KRİTİK HATA: Odds analizi modeli değiştirdi."
            )

        if not self.snapshot.locked:
            raise RuntimeError(
                "KRİTİK HATA: Model LOCK durumu kayboldu."
            )

        # =================================================
        # RESULT
        # =================================================

        return AnalysisResult(
            snapshot=self.snapshot,
            fair_odds=fair_odds,
            no_vig_probabilities=no_vig,
            ev=baseline_ev,
            stress_lambdas=stress_lambdas_result,
            stress_probabilities=stress_probabilities_result,
            pessimistic_probabilities=(
                pessimistic_probabilities
            ),
            pessimistic_ev=pessimistic_ev,
            selections=selections,
        )


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def run_pipeline(
    stats: TeamStats,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Q200 V3.1 pipeline convenience wrapper.
    """

    pipeline = Q200Pipeline(
        stats
    )

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )
