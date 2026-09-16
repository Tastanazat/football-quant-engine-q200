"""
Q200 Engine - Analysis History

Q200 V3.1

Q200 analiz raporlarını kalıcı SQLite veritabanında saklar.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection değiştirmez.
- Kayıtlı analiz verisini değiştirmez.
- Maç sonucunu kaydeder.
- Settlement sonucunu kalıcı olarak saklar.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report import build_report


HISTORY_SCHEMA_VERSION = "Q200-HISTORY-V3"


def _validate_text(
    value: Any,
    name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{name} string olmalıdır."
        )

    result = value.strip()

    if not result:
        raise ValueError(
            f"{name} boş olamaz."
        )

    return result


def _validate_goals(
    value: Any,
    name: str,
) -> int:

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            f"{name} integer olmalıdır."
        )

    if not isinstance(
        value,
        int,
    ):
        raise TypeError(
            f"{name} integer olmalıdır."
        )

    if value < 0:
        raise ValueError(
            f"{name} negatif olamaz."
        )

    return value


def _utc_now() -> str:

    return datetime.now(
        timezone.utc
    ).isoformat()


class AnalysisHistory:
    """
    Q200 analiz geçmişi için SQLite repository.
    """

    def __init__(
        self,
        path: str | Path,
    ):

        self.path = Path(path)

        if (
            self.path.exists()
            and self.path.is_dir()
        ):
            raise ValueError(
                "History path bir dosya olmalıdır: "
                f"{self.path}"
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(
        self,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    result_recorded INTEGER NOT NULL DEFAULT 0,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    result_recorded_at TEXT,
                    settlement_recorded INTEGER NOT NULL DEFAULT 0,
                    settlement_json TEXT,
                    settlement_recorded_at TEXT
                )
                """
            )

            self._ensure_column(
                connection,
                "result_recorded",
                "INTEGER NOT NULL DEFAULT 0",
            )

            self._ensure_column(
                connection,
                "home_goals",
                "INTEGER",
            )

            self._ensure_column(
                connection,
                "away_goals",
                "INTEGER",
            )

            self._ensure_column(
                connection,
                "result_recorded_at",
                "TEXT",
            )

            self._ensure_column(
                connection,
                "settlement_recorded",
                "INTEGER NOT NULL DEFAULT 0",
            )

            self._ensure_column(
                connection,
                "settlement_json",
                "TEXT",
            )

            self._ensure_column(
                connection,
                "settlement_recorded_at",
                "TEXT",
            )

            connection.commit()

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        column_name: str,
        column_definition: str,
    ) -> None:

        columns = connection.execute(
            """
            PRAGMA table_info(
                analysis_history
            )
            """
        ).fetchall()

        existing_columns = {
            row["name"]
            for row in columns
        }

        if column_name not in existing_columns:

            connection.execute(
                f"""
                ALTER TABLE analysis_history
                ADD COLUMN {column_name}
                {column_definition}
                """
            )

    def save(
        self,
        result,
        match_id: str,
    ) -> int:
        """
        AnalysisResult'ı geçmişe kaydeder
        ve kayıt ID'sini döndürür.
        """

        match_id = _validate_text(
            match_id,
            "match_id",
        )

        report = build_report(
            result
        )

        report_json = json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=False,
        )

        created_at = _utc_now()

        with self._connect() as connection:

            cursor = connection.execute(
                """
                INSERT INTO analysis_history (
                    match_id,
                    created_at,
                    report_version,
                    model_version,
                    report_json,
                    result_recorded,
                    home_goals,
                    away_goals,
                    result_recorded_at,
                    settlement_recorded,
                    settlement_json,
                    settlement_recorded_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, 0,
                    NULL, NULL, NULL,
                    0, NULL, NULL
                )
                """,
                (
                    match_id,
                    created_at,
                    report["report_version"],
                    report["model_version"],
                    report_json,
                ),
            )

            connection.commit()

            return int(
                cursor.lastrowid
            )

    def record_result(
        self,
        record_id: int,
        home_goals: int,
        away_goals: int,
    ) -> bool:
        """
        Kayıtlı analize maç sonucunu ekler.

        Yeni sonuç kaydedildiğinde daha önce hesaplanmış
        settlement otomatik olarak geçersiz hale getirilir.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        home_goals = _validate_goals(
            home_goals,
            "home_goals",
        )

        away_goals = _validate_goals(
            away_goals,
            "away_goals",
        )

        recorded_at = _utc_now()

        with self._connect() as connection:

            cursor = connection.execute(
                """
                UPDATE analysis_history
                SET
                    result_recorded = 1,
                    home_goals = ?,
                    away_goals = ?,
                    result_recorded_at = ?,
                    settlement_recorded = 0,
                    settlement_json = NULL,
                    settlement_recorded_at = NULL
                WHERE id = ?
                """,
                (
                    home_goals,
                    away_goals,
                    recorded_at,
                    record_id,
                ),
            )

            connection.commit()

            return (
                cursor.rowcount == 1
            )

    def record_settlement(
        self,
        record_id: int,
        settlement: dict[str, Any],
    ) -> bool:
        """
        Hesaplanmış settlement sonucunu History kaydına
        kalıcı olarak yazar.

        Settlement yalnızca maç sonucu zaten kaydedilmişse
        yazılabilir.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        if not isinstance(
            settlement,
            dict,
        ):
            raise TypeError(
                "settlement dictionary olmalıdır."
            )

        required = (
            "record_id",
            "match_id",
            "home_goals",
            "away_goals",
            "selections",
            "summary",
        )

        missing = [
            field
            for field in required
            if field not in settlement
        ]

        if missing:
            raise ValueError(
                "Settlement eksik alan içeriyor: "
                + ", ".join(missing)
            )

        if settlement["record_id"] != record_id:
            raise ValueError(
                "Settlement record_id ile History record_id eşleşmiyor."
            )

        home_goals = _validate_goals(
            settlement["home_goals"],
            "home_goals",
        )

        away_goals = _validate_goals(
            settlement["away_goals"],
            "away_goals",
        )

        settlement_json = json.dumps(
            settlement,
            ensure_ascii=False,
            sort_keys=False,
        )

        recorded_at = _utc_now()

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT
                    result_recorded,
                    home_goals,
                    away_goals
                FROM analysis_history
                WHERE id = ?
                """,
                (
                    record_id,
                ),
            ).fetchone()

            if row is None:
                return False

            if not bool(
                row["result_recorded"]
            ):
                raise ValueError(
                    "Settlement için önce maç sonucu kaydedilmelidir."
                )

            if (
                row["home_goals"]
                != home_goals
                or row["away_goals"]
                != away_goals
            ):
                raise ValueError(
                    "Settlement skoru History'deki maç sonucu ile eşleşmiyor."
                )

            cursor = connection.execute(
                """
                UPDATE analysis_history
                SET
                    settlement_recorded = 1,
                    settlement_json = ?,
                    settlement_recorded_at = ?
                WHERE id = ?
                """,
                (
                    settlement_json,
                    recorded_at,
                    record_id,
                ),
            )

            connection.commit()

            return (
                cursor.rowcount == 1
            )

    def settle_record(
        self,
        record_id: int,
    ) -> dict[str, Any]:
        """
        History kaydındaki kayıtlı maç sonucu ile
        settlement hesaplar ve sonucu SQLite'a
        kalıcı olarak kaydeder.
        """

        record = self.get(
            record_id
        )

        if record is None:
            raise ValueError(
                f"History kaydı bulunamadı: {record_id}"
            )

        if not record[
            "result_recorded"
        ]:
            raise ValueError(
                "Settlement için önce maç sonucu kaydedilmelidir."
            )

        from .settlement import (
            settle_analysis_record,
        )

        settlement = (
            settle_analysis_record(
                record,
                record["home_goals"],
                record["away_goals"],
            )
        )

        self.record_settlement(
            record_id,
            settlement,
        )

        return settlement

    def get(
        self,
        record_id: int,
    ) -> dict[str, Any] | None:
        """
        ID ile tek geçmiş kaydını getirir.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT
                    id,
                    match_id,
                    created_at,
                    report_version,
                    model_version,
                    report_json,
                    result_recorded,
                    home_goals,
                    away_goals,
                    result_recorded_at,
                    settlement_recorded,
                    settlement_json,
                    settlement_recorded_at
                FROM analysis_history
                WHERE id = ?
                """,
                (
                    record_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "match_id": row["match_id"],
            "created_at": row["created_at"],
            "report_version": row["report_version"],
            "model_version": row["model_version"],
            "report": json.loads(
                row["report_json"]
            ),
            "result_recorded": bool(
                row["result_recorded"]
            ),
            "home_goals": row[
                "home_goals"
            ],
            "away_goals": row[
                "away_goals"
            ],
            "result_recorded_at": row[
                "result_recorded_at"
            ],
            "settlement_recorded": bool(
                row["settlement_recorded"]
            ),
            "settlement": (
                json.loads(
                    row["settlement_json"]
                )
                if row["settlement_json"]
                else None
            ),
            "settlement_recorded_at": row[
                "settlement_recorded_at"
            ],
        }

    def list(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        En yeni analizleri listeler.
        """

        if not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit integer olmalıdır."
            )

        if limit <= 0:
            raise ValueError(
                "limit pozitif olmalıdır."
            )

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    match_id,
                    created_at,
                    report_version,
                    model_version,
                    result_recorded,
                    home_goals,
                    away_goals,
                    result_recorded_at,
                    settlement_recorded,
                    settlement_recorded_at
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    limit,
                ),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "match_id": row["match_id"],
                "created_at": row["created_at"],
                "report_version": row[
                    "report_version"
                ],
                "model_version": row[
                    "model_version"
                ],
                "result_recorded": bool(
                    row["result_recorded"]
                ),
                "home_goals": row[
                    "home_goals"
                ],
                "away_goals": row[
                    "away_goals"
                ],
                "result_recorded_at": row[
                    "result_recorded_at"
                ],
                "settlement_recorded": bool(
                    row["settlement_recorded"]
                ),
                "settlement_recorded_at": row[
                    "settlement_recorded_at"
                ],
            }
            for row in rows
        ]

    def count(
        self,
    ) -> int:
        """
        Toplam kayıt sayısını döndürür.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM analysis_history
                """
            ).fetchone()

        return int(
            row["count"]
        )

    def count_completed(
        self,
    ) -> int:
        """
        Sonucu kaydedilmiş analizlerin
        toplam sayısını döndürür.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM analysis_history
                WHERE result_recorded = 1
                """
            ).fetchone()

        return int(
            row["count"]
        )

    def delete(
        self,
        record_id: int,
    ) -> bool:
        """
        Bir geçmiş kaydını siler.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        with self._connect() as connection:

            cursor = connection.execute(
                """
                DELETE FROM analysis_history
                WHERE id = ?
                """,
                (
                    record_id,
                ),
            )

            connection.commit()

            return (
                cursor.rowcount == 1
            )
