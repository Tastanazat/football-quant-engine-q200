"""
Q200 Engine - StatsHub Review Mapper

Q200 V3.1

StatsHub OCR
      ↓
DataReview
      ↓
Approved Data
      ↓
StatsHubData

Bu katman:
- DataReview sonucunu StatsHubData'ya dönüştürür.
- Manuel düzeltmeleri korur.
- İlk OCR değerlerini kaybetmez.
- Sadece onaylanmış veriyi ingestion katmanına geçirir.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds kullanmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
"""

from __future__ import annotations

from typing import Any

from .data_review import DataReview
from .ingestion.models import (
    MatchInfo,
    StatsHubData,
)


STATSHUB_REVIEW_MAPPER_VERSION = (
    "Q200-STATSHUB-REVIEW-MAPPER-V1"
)


def review_to_statshub_data(
    review: DataReview,
    *,
    match: MatchInfo | None = None,
) -> StatsHubData:
    """
    Onaylanmış DataReview sonucunu StatsHubData'ya çevirir.

    ÖNEMLİ:

    DataReview onaylanmamışsa ingestion'a geçişe
    izin verilmez.

    Manuel düzeltilmiş değerler:
        review.fields[field].value

    İlk OCR değerleri:
        review.fields[field].raw_value

    olarak ayrı ayrı korunur.
    """

    if not isinstance(
        review,
        DataReview,
    ):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    if not review.approved:
        raise RuntimeError(
            "StatsHub verisi ingestion'a "
            "aktarılmadan önce DataReview "
            "onaylanmalıdır."
        )

    values = review.values(
        require_approved=True
    )

    if not values:
        raise ValueError(
            "Onaylanmış StatsHub review "
            "boş olamaz."
        )

    raw_values = review.raw_values()

    source_metadata: dict[str, Any] = {
        "mapper_version":
            STATSHUB_REVIEW_MAPPER_VERSION,
        "source":
            "StatsHub",
        "review_id":
            review.review_id,
        "review_status":
            review.review_status(),
        "approved":
            review.approved,
        "raw_values":
            raw_values,
        "changed_fields":
            list(review.changed_fields),
        "manual_field_count":
            review.manual_field_count,
        "ocr_field_count":
            len(review.fields),
    }

    if review.metadata:
        source_metadata[
            "review_metadata"
        ] = dict(review.metadata)

    return StatsHubData(
        match=match,
        values=dict(values),
        raw_text=review.metadata.get(
            "ocr_text"
        ),
        source_metadata=source_metadata,
    )


def merge_reviewed_statshub_into_canonical(
    review: DataReview,
    *,
    match: MatchInfo,
    soccerstats: Any | None = None,
):
    """
    Onaylanmış StatsHub Review'ını Source Mapper'a bağlar.

    SoccerSTATS varsa Source Mapper'ın mevcut
    öncelik kuralı korunur.

    SoccerSTATS yoksa StatsHub değerleri
    canonical data'ya aktarılır.
    """

    if not isinstance(
        match,
        MatchInfo,
    ):
        raise TypeError(
            "match MatchInfo olmalıdır."
        )

    statshub = review_to_statshub_data(
        review,
        match=match,
    )

    from .ingestion.source_mapper import (
        map_sources,
    )

    return map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
    )


__all__ = [
    "STATSHUB_REVIEW_MAPPER_VERSION",
    "review_to_statshub_data",
    "merge_reviewed_statshub_into_canonical",
]
