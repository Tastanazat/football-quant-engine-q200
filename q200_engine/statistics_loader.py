"""
Q200 Engine - Statistics Loader

Q200 V3.1

İki ayrı CSV/XLSX statistics dosyasını Q200 veri akışına bağlar.

Akış:

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

Kural:

Statistics File 1 > Statistics File 2

Bu katman:
- Odds kullanmaz.
- Model hesabı yapmaz.
- Model olasılığı üretmez.
- Statistics değerlerini değiştirmez.
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
    İki statistics dosyasından seçilen kayıtları okuyup TeamStats üretir.

    Öncelik:

        File 1 > File 2

    Her dosya CSV veya XLSX olabilir.

    Dosyalardan biri bir alanı içermiyorsa, diğer dosyadaki alan
    adapter tarafından kullanılabilir. Aynı alan iki dosyada da
    varsa File 1 değeri kullanılır.
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
