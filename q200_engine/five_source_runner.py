"""
Q200 Engine - Five Source Runner

Q200 V3.1

Amaç
-----

Beş gerçek kaynak dosyasını tek giriş noktasından
Q200 FiveSourceMatchInput sözleşmesine bağlamak.

Kaynaklar:

    1. StatsHub HOME image
    2. StatsHub AWAY image
    3. SoccerSTATS PDF
    4. PPI PDF
    5. Odds PDF

Akış:

    Dosyalar
        ↓
    Five Source Loader
        ↓
    FiveSourceMatchInput
        ↓
    Five Source Pipeline
        ↓
    Q200Pipeline
        ↓
    MODEL LOCK
        ↓
    ODDS ANALYSIS
        ↓
    AnalysisResult

KRİTİK KURALLAR
---------------

Bu katman:

- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Selection hesaplamaz.
- Kelly hesaplamaz.
- Model oluşturma mantığını değiştirmez.
- Odds'u model oluşturma aşamasında kullanmaz.

Bu katmanın görevi yalnızca gerçek kaynak
dosyalarını mevcut Five Source altyapısına bağlamaktır.
"""

from __future__ import annotations

from pathlib import Path

from .five_source_loader import (
    build_five_source_input,
    load_ppi_pdf,
    load_statshub_image,
)
from .five_source_pipeline import (
    run_five_source_analysis,
)
from .ingestion.models import (
    MatchInfo,
)
from .schema import (
    AnalysisResult,
)


FIVE_SOURCE_RUNNER_VERSION = (
    "Q200-FIVE-SOURCE-RUNNER-V1"
)


def run_five_source_files(
    *,
    match: MatchInfo,
    statshub_home_image: str | Path,
    statshub_away_image: str | Path,
    soccerstats_pdf: str | Path,
    ppi_pdf: str | Path,
    odds_pdf: str | Path,
    bankroll: float,
    market: str = "1X2",
    uncertainty: str = "MEDIUM",
    home_ocr_text: str | None = None,
    away_ocr_text: str | None = None,
) -> AnalysisResult:
    """
    Beş gerçek kaynak dosyasından Q200 analizini çalıştırır.

    Kaynak sırası:

        StatsHub HOME
        StatsHub AWAY
        SoccerSTATS
        PPI
        Odds

    Önce statistics kaynakları hazırlanır ve
    FiveSourceMatchInput oluşturulur.

    Daha sonra mevcut Five Source Pipeline çağrılır.

    Model oluşturma ve model lock işlemleri bu
    fonksiyon tarafından yapılmaz.

    Parameters
    ----------
    match:
        Ana maç kimliği.

    statshub_home_image:
        StatsHub HOME ekran görüntüsü.

    statshub_away_image:
        StatsHub AWAY ekran görüntüsü.

    soccerstats_pdf:
        SoccerSTATS PDF dosyası.

    ppi_pdf:
        PPI PDF dosyası.

    odds_pdf:
        Odds PDF dosyası.

    bankroll:
        Selection / Kelly için bankroll.

    market:
        Analiz edilecek odds marketi.

    uncertainty:
        Q200 uncertainty seviyesi.

    home_ocr_text:
        İsteğe bağlı önceden çıkarılmış HOME OCR metni.

    away_ocr_text:
        İsteğe bağlı önceden çıkarılmış AWAY OCR metni.

    Returns
    -------
    AnalysisResult
        Mevcut Q200 analiz sonucu.
    """

    # ---------------------------------------------------------
    # MATCH VALIDATION
    # ---------------------------------------------------------

    if not isinstance(
        match,
        MatchInfo,
    ):
        raise TypeError(
            "match MatchInfo olmalıdır."
        )

    # ---------------------------------------------------------
    # STATSHUB HOME
    # ---------------------------------------------------------

    statshub_home = load_statshub_image(
        statshub_home_image,
        match=match,
        ocr_text=home_ocr_text,
    )

    # ---------------------------------------------------------
    # STATSHUB AWAY
    # ---------------------------------------------------------

    statshub_away = load_statshub_image(
        statshub_away_image,
        match=match,
        ocr_text=away_ocr_text,
    )

    # ---------------------------------------------------------
    # PPI
    # ---------------------------------------------------------

    ppi = load_ppi_pdf(
        ppi_pdf,
        match=match,
    )

    # ---------------------------------------------------------
    # FIVE SOURCE INPUT
    # ---------------------------------------------------------

    data = build_five_source_input(
        match=match,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        soccerstats_pdf=soccerstats_pdf,
        ppi_pdf=ppi_pdf,
        odds_pdf=odds_pdf,
    )

    # ---------------------------------------------------------
    # FINAL FIVE SOURCE ANALYSIS
    # ---------------------------------------------------------

    result = run_five_source_analysis(
        data,
        market=market,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )

    # ---------------------------------------------------------
    # FINAL INTEGRITY CHECK
    # ---------------------------------------------------------

    if not result.snapshot.locked:
        raise RuntimeError(
            "Five-source runner locked model "
            "üretemedi."
        )

    return result


__all__ = [
    "FIVE_SOURCE_RUNNER_VERSION",
    "run_five_source_files",
]
