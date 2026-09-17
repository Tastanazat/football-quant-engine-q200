"""
Q200 Engine - Statistics Loader

Q200 V3.1

İki ayrı statistics dosyasını Q200 veri akışına bağlar.

Normal akış:

STATISTICS FILE 1
        +
STATISTICS FILE 2
        ↓
Statistics Reader
        ↓
Statistics Adapter
        ↓
Input Validation
        ↓
TeamStats

Data Review akışı:

STATISTICS FILE 1
        ↓
Data Review 1
        ↓
MANUAL CORRECTION
        ↓
APPROVAL

STATISTICS FILE 2
        ↓
Data Review 2
        ↓
MANUAL CORRECTION
        ↓
APPROVAL

        ↓
Statistics Adapter
        ↓
TeamStats

Kural:

Statistics File 1 > Statistics File 2
"""

from __future__ import annotations

from pathlib import Path

from .schema import TeamStats
from .statistics_adapter import adapt_statistics_sources
from .statistics_reader import read_statistics_record


def load_team_stats(
    statistics_file_1: str | Path,
    statistics_file_2: str | Path,
    row_index_1: int = 0,
    row_index_2: int = 0,
) -> TeamStats:
    """
    İki statistics dosyasından seçilen kayıtları okuyup
    TeamStats üretir.

    Bu eski/otomatik akıştır.

    Öncelik:

        File 1 > File 2
    """

    statistics_1 = read_statistics_record(
        statistics_file_1,
        row_index=row_index_1,
    )

    statistics_2 = read_statistics_record(
        statistics_file_2,
        row_index=row_index_2,
    )

    return adapt_statistics_sources(
        statistics_1,
        statistics_2,
    )


# =========================================================
# DATA REVIEW LOADER
# =========================================================

def load_team_stats_from_reviews(
    review_1,
    review_2,
) -> TeamStats:
    """
    Onaylanmış iki DataReview nesnesinden TeamStats üretir.

    Manuel kontrol kapısı:

        Review 1 approved
        +
        Review 2 approved
        ↓
        TeamStats

    Review'lardan biri bile onaylanmamışsa
    model verisi oluşturulmaz.

    Öncelik:

        Review 1 > Review 2
    """

    from .data_review import (
        DataReview,
        reviewed_values,
    )

    if not isinstance(
        review_1,
        DataReview,
    ):
        raise TypeError(
            "review_1 DataReview olmalıdır."
        )

    if not isinstance(
        review_2,
        DataReview,
    ):
        raise TypeError(
            "review_2 DataReview olmalıdır."
        )

    statistics_1 = reviewed_values(
        review_1
    )

    statistics_2 = reviewed_values(
        review_2
    )

    return adapt_statistics_sources(
        statistics_1,
        statistics_2,
    )
