"""
Q200 Engine - Data Review

Q200 V3.1

Dosya / OCR / PDF okuma sonucunun Q200 modeline girmeden
önce kullanıcı tarafından kontrol edilmesini sağlar.

AKIŞ:

RAW FILE / OCR / PDF
        ↓
READ RESULT
        ↓
DATA REVIEW
        ↓
AUTO / MANUAL
        ↓
USER APPROVAL
        ↓
CANONICAL DATA
        ↓
Q200 MODEL

ÖNEMLİ:
- Orijinal OCR/PDF değeri korunur.
- Manuel düzeltme ayrı tutulur.
- Manuel değişiklik review'ı tekrar onaysız yapar.
- Onaylanmamış veri modele gönderilemez.
- Confidence bilgisi korunur.
- Review çıktısı JSON olarak dışarı aktarılabilir.
"""

from __future__ import annotations

import copy
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


DATA_REVIEW_VERSION = "Q200-DATA-REVIEW-V1"

SOURCE_TYPES = {
    "OCR",
    "PDF",
    "CSV",
    "XLSX",
    "MANUAL",
    "OTHER",
}

VALUE_STATUSES = {
    "AUTO",
    "MANUAL",
}


@dataclass
class ReviewField:
    """Tek bir veri alanının okuma ve düzeltme bilgisi."""

    field: str
    raw_value: Any
    value: Any
    source: str = "OTHER"
    confidence: float | None = None
    status: str = "AUTO"
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.field, str) or not self.field.strip():
            raise ValueError("Review field adı boş olamaz.")

        self.field = self.field.strip().lower()

        if self.source not in SOURCE_TYPES:
            raise ValueError(
                f"Geçersiz review source: {self.source}"
            )

        if self.status not in VALUE_STATUSES:
            raise ValueError(
                f"Geçersiz review status: {self.status}"
            )

        if self.confidence is not None:
            if isinstance(self.confidence, bool):
                raise ValueError(
                    "confidence boolean olamaz."
                )

            try:
                confidence = float(self.confidence)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "confidence 0-1 arasında sayı olmalıdır."
                ) from exc

            if (
                not math.isfinite(confidence)
                or not 0 <= confidence <= 1
            ):
                raise ValueError(
                    "confidence 0-1 arasında sonlu sayı olmalıdır."
                )

            self.confidence = confidence


@dataclass
class DataReview:
    """
    Bir dosya okuma sonucu için manuel kontrol oturumu.

    Örnek:

        OCR → shots = 14
        kullanıcı → shots = 15

    raw_value = 14
    value     = 15
    status    = MANUAL
    approved  = False
    """

    review_id: str
    source_type: str
    source_file: str
    fields: dict[str, ReviewField] = field(default_factory=dict)
    approved: bool = False
    version: str = DATA_REVIEW_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or not self.review_id.strip()
        ):
            raise ValueError(
                "review_id boş olamaz."
            )

        if self.source_type not in SOURCE_TYPES:
            raise ValueError(
                f"Geçersiz review source_type: "
                f"{self.source_type}"
            )

        if (
            not isinstance(self.source_file, str)
            or not self.source_file.strip()
        ):
            raise ValueError(
                "source_file boş olamaz."
            )

        if self.version != DATA_REVIEW_VERSION:
            raise ValueError(
                f"Desteklenmeyen Data Review sürümü: "
                f"{self.version}"
            )

    @property
    def is_approved(self) -> bool:
        return self.approved

    @property
    def field_count(self) -> int:
        return len(self.fields)

    @property
    def manual_field_count(self) -> int:
        return sum(
            1
            for item in self.fields.values()
            if item.status == "MANUAL"
        )

    @property
    def auto_field_count(self) -> int:
        return sum(
            1
            for item in self.fields.values()
            if item.status == "AUTO"
        )

    @property
    def low_confidence_fields(self) -> list[str]:
        return [
            name
            for name, item in self.fields.items()
            if (
                item.confidence is not None
                and item.confidence < 0.80
            )
        ]

    @property
    def changed_fields(self) -> list[str]:
        return [
            name
            for name, item in self.fields.items()
            if item.status == "MANUAL"
        ]

    def set_field(
        self,
        field: str,
        value: Any,
        *,
        source: str | None = None,
        confidence: float | None = None,
        note: str | None = None,
    ) -> ReviewField:
        """
        Alanı manuel olarak değiştirir.

        Manuel değişiklik:
        - raw_value'yu korur.
        - value'yu değiştirir.
        - status = MANUAL yapar.
        - approval'ı iptal eder.
        """

        if not isinstance(field, str):
            raise TypeError(
                "field string olmalıdır."
            )

        normalized = field.strip().lower()

        if not normalized:
            raise ValueError(
                "field adı boş olamaz."
            )

        existing = self.fields.get(normalized)

        if existing is None:
            review_field = ReviewField(
                field=normalized,
                raw_value=value,
                value=value,
                source=source or "MANUAL",
                confidence=confidence,
                status="MANUAL",
                note=note,
            )
        else:
            review_field = ReviewField(
                field=normalized,
                raw_value=existing.raw_value,
                value=value,
                source=source or existing.source,
                confidence=(
                    confidence
                    if confidence is not None
                    else existing.confidence
                ),
                status="MANUAL",
                note=note,
            )

        self.fields[normalized] = review_field

        # Her manuel değişiklik yeniden kontrol gerektirir.
        self.approved = False

        return review_field

    def approve(self) -> None:
        """
        Review'ı onaylar.

        Boş veri onaylanamaz.
        """

        if not self.fields:
            raise ValueError(
                "Boş review onaylanamaz."
            )

        self.approved = True

    def revoke_approval(self) -> None:
        """Review onayını geri alır."""

        self.approved = False

    def values(
        self,
        *,
        require_approved: bool = True,
    ) -> dict[str, Any]:
        """
        Son değerleri döndürür.

        require_approved=True ise sadece onaylanmış
        veri modele gönderilebilir.
        """

        if require_approved and not self.approved:
            raise RuntimeError(
                "Data Review onaylanmadan değerler "
                "modele gönderilemez."
            )

        return {
            name: item.value
            for name, item in self.fields.items()
        }

    def raw_values(self) -> dict[str, Any]:
        """İlk okunan ham değerleri döndürür."""

        return {
            name: item.raw_value
            for name, item in self.fields.items()
        }

    def review_status(self) -> str:
        """
        Kullanıcı arayüzü için genel durum.
        """

        if self.approved:
            return "APPROVED"

        if self.manual_field_count > 0:
            return "MANUAL_REVIEW_REQUIRED"

        if self.low_confidence_fields:
            return "LOW_CONFIDENCE_REVIEW_REQUIRED"

        return "REVIEW_REQUIRED"

    def to_dict(self) -> dict[str, Any]:
        """Review'ı JSON uyumlu dictionary yapar."""

        result = asdict(self)

        result["fields"] = {
            name: asdict(item)
            for name, item in self.fields.items()
        }

        return copy.deepcopy(result)


def create_review(
    *,
    review_id: str,
    source_type: str,
    source_file: str,
    values: Mapping[str, Any],
    confidence: Mapping[str, float] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DataReview:
    """
    OCR/PDF/CSV/XLSX okuma sonucundan DataReview oluşturur.

    Başlangıçta bütün alanlar AUTO durumundadır.
    """

    if not isinstance(values, Mapping):
        raise TypeError(
            "values Mapping olmalıdır."
        )

    confidence_map = dict(confidence or {})

    review = DataReview(
        review_id=review_id,
        source_type=source_type,
        source_file=source_file,
        metadata=dict(metadata or {}),
    )

    for raw_name, value in values.items():
        if (
            not isinstance(raw_name, str)
            or not raw_name.strip()
        ):
            raise ValueError(
                "Review field adı boş olamaz."
            )

        name = raw_name.strip().lower()

        field_confidence = confidence_map.get(
            raw_name
        )

        if field_confidence is None:
            field_confidence = confidence_map.get(
                name
            )

        review.fields[name] = ReviewField(
            field=name,
            raw_value=value,
            value=value,
            source=source_type,
            confidence=field_confidence,
            status="AUTO",
        )

    if not review.fields:
        raise ValueError(
            "Data Review için en az bir alan gereklidir."
        )

    return review


def update_review_field(
    review: DataReview,
    field: str,
    value: Any,
    *,
    note: str | None = None,
    confidence: float | None = None,
) -> DataReview:
    """Bir alanı manuel olarak düzeltir."""

    if not isinstance(review, DataReview):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    review.set_field(
        field,
        value,
        note=note,
        confidence=confidence,
    )

    return review


def approve_review(
    review: DataReview,
) -> DataReview:
    """Review'ı onaylar."""

    if not isinstance(review, DataReview):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    review.approve()

    return review


def revoke_review(
    review: DataReview,
) -> DataReview:
    """Review onayını kaldırır."""

    if not isinstance(review, DataReview):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    review.revoke_approval()

    return review


def reviewed_values(
    review: DataReview,
) -> dict[str, Any]:
    """
    Sadece onaylanmış değerleri modele aktarır.
    """

    if not isinstance(review, DataReview):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    return review.values(
        require_approved=True
    )


def review_to_dict(
    review: DataReview,
) -> dict[str, Any]:
    """Public dictionary serializer."""

    if not isinstance(review, DataReview):
        raise TypeError(
            "review DataReview olmalıdır."
        )

    return review.to_dict()
