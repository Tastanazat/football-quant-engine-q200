"""
Q200 Engine - Streamlit Application

Q200 V3.1

Kullanıcı arayüzü.

Ana akış:

Maç Bilgileri
        ↓
StatsHub HOME
StatsHub AWAY
        ↓
SoccerSTATS PDF
PPI PDF
Odds PDF
        ↓
Five Source Input
        ↓
Q200 Model
        ↓
MODEL LOCK
        ↓
Odds Analysis
        ↓
Report
        ↓
History
        ↓
Match Result
        ↓
Settlement
        ↓
Evaluation
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from q200_engine.five_source_loader import (
    build_five_source_input,
    load_ppi_pdf,
    load_statshub_text,
)

from q200_engine.five_source_pipeline import (
    run_five_source_analysis,
)

from q200_engine.ingestion.models import (
    MatchInfo,
)

from q200_engine.ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)

from q200_engine.odds_pdf_reader import (
    parse_odds_pdf,
)

from q200_engine.report import (
    build_report,
    report_to_json,
    report_to_text,
)

from q200_engine.history import (
    AnalysisHistory,
)

from q200_engine.settlement import (
    settle_analysis_record,
)

from q200_engine.evaluation import (
    build_evaluation,
    evaluation_to_json,
    evaluation_to_text,
)


APP_VERSION = "Q200-STREAMLIT-V2"

HISTORY_PATH = Path(
    "q200_history.sqlite3"
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Q200 Football Quant Engine",
    page_icon="⚽",
    layout="wide",
)


# =========================================================
# HISTORY
# =========================================================

@st.cache_resource
def get_history() -> AnalysisHistory:
    """
    Kalıcı Q200 History repository.

    SQLite dosyası proje çalışma dizininde tutulur.
    """

    return AnalysisHistory(
        HISTORY_PATH
    )


history = get_history()


# =========================================================
# HELPERS
# =========================================================

def save_uploaded_file(
    uploaded_file,
) -> Path:
    """
    Streamlit UploadedFile nesnesini
    geçici dosyaya yazar.
    """

    suffix = Path(
        uploaded_file.name
    ).suffix

    temporary = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    temporary.write(
        uploaded_file.getbuffer()
    )

    temporary.close()

    return Path(
        temporary.name
    )


def _format_money(
    value,
) -> str:
    """
    Para değerini okunabilir gösterir.
    """

    try:
        return f"{float(value):,.2f}"
    except (
        TypeError,
        ValueError,
    ):
        return "-"


def _format_percent(
    value,
) -> str:
    """
    Oran değerini yüzde olarak gösterir.
    """

    try:
        return f"{float(value):.2%}"
    except (
        TypeError,
        ValueError,
    ):
        return "-"


def show_result(
    result,
) -> None:
    """
    Q200 sonucunu kullanıcıya gösterir.
    """

    st.subheader(
        "Q200 Analiz Sonucu"
    )

    snapshot = result.snapshot

    # -----------------------------------------------------
    # MODEL
    # -----------------------------------------------------

    st.success(
        "MODEL LOCK: AKTİF"
        if snapshot.locked
        else "MODEL LOCK: AKTİF DEĞİL"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Lambda Home",
            f"{snapshot.lambda_home:.4f}",
        )

    with col2:
        st.metric(
            "Lambda Away",
            f"{snapshot.lambda_away:.4f}",
        )

    with col3:
        st.metric(
            "Model",
            snapshot.model_version,
        )

    # -----------------------------------------------------
    # MODEL PROBABILITIES
    # -----------------------------------------------------

    st.subheader(
        "Model Olasılıkları"
    )

    model_rows = []

    for outcome, probability in (
        snapshot.probabilities.items()
    ):
        model_rows.append(
            {
                "Outcome": outcome,
                "Probability": (
                    f"{probability:.2%}"
                ),
            }
        )

    st.table(
        model_rows
    )

    # -----------------------------------------------------
    # FAIR ODDS / NO-VIG
    # -----------------------------------------------------

    st.subheader(
        "Fair Odds / No-Vig"
    )

    odds_rows = []

    outcomes = set(
        result.fair_odds.keys()
    )

    outcomes.update(
        result.no_vig_probabilities.keys()
    )

    outcomes.update(
        result.ev.keys()
    )

    for outcome in sorted(
        outcomes
    ):
        fair = result.fair_odds.get(
            outcome
        )

        no_vig = (
            result.no_vig_probabilities.get(
                outcome
            )
        )

        ev = result.ev.get(
            outcome
        )

        odds_rows.append(
            {
                "Outcome": outcome,
                "No-Vig": (
                    f"{no_vig:.2%}"
                    if no_vig is not None
                    else "-"
                ),
                "Fair Odds": (
                    f"{fair:.3f}"
                    if fair is not None
                    else "-"
                ),
                "EV": (
                    f"{ev:+.2%}"
                    if ev is not None
                    else "-"
                ),
            }
        )

    st.table(
        odds_rows
    )

    # -----------------------------------------------------
    # PESSIMISTIC
    # -----------------------------------------------------

    st.subheader(
        "Pessimistic Analysis"
    )

    pessimistic_rows = []

    for outcome, probability in (
        result.pessimistic_probabilities.items()
    ):
        pessimistic_rows.append(
            {
                "Outcome": outcome,
                "Probability": (
                    f"{probability:.2%}"
                ),
                "Pessimistic EV": (
                    f"{result.pessimistic_ev.get(outcome, 0.0):+.2%}"
                ),
            }
        )

    if pessimistic_rows:
        st.table(
            pessimistic_rows
        )
    else:
        st.info(
            "Pessimistic sonuç bulunamadı."
        )

    # -----------------------------------------------------
    # SELECTION
    # -----------------------------------------------------

    st.subheader(
        "Selection"
    )

    if not result.selections:
        st.info(
            "Seçim bulunamadı."
        )

    else:

        selection_rows = []

        for selection in (
            result.selections
        ):
            selection_rows.append(
                {
                    "Outcome": selection.get(
                        "outcome",
                        "",
                    ),
                    "Eligible": selection.get(
                        "eligible",
                        False,
                    ),
                    "Odds": selection.get(
                        "odds",
                        "",
                    ),
                    "Stake": selection.get(
                        "stake",
                        0.0,
                    ),
                    "Reason": selection.get(
                        "reason",
                        "",
                    ),
                }
            )

        st.dataframe(
            selection_rows,
            use_container_width=True,
        )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    st.subheader(
        "Rapor"
    )

    report = build_report(
        result
    )

    json_text = report_to_json(
        result
    )

    text_report = report_to_text(
        result
    )

    tab_text, tab_json = st.tabs(
        [
            "TXT",
            "JSON",
        ]
    )

    with tab_text:

        st.code(
            text_report,
            language="text",
        )

        st.download_button(
            label="TXT Raporunu İndir",
            data=text_report,
            file_name="q200_report.txt",
            mime="text/plain",
        )

    with tab_json:

        st.code(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            ),
            language="json",
        )

        st.download_button(
            label="JSON Raporunu İndir",
            data=json_text,
            file_name="q200_report.json",
            mime="application/json",
        )


# =========================================================
# HISTORY UI
# =========================================================

def show_history_section() -> None:
    """
    Kalıcı analiz geçmişini gösterir.

    Burada yeni model hesabı yapılmaz.

    History yalnızca mevcut kayıtları okur,
    maç sonucunu kaydeder ve settlement çalıştırır.
    """

    st.header(
        "5. Analysis History"
    )

    total_records = history.count()

    completed_records = (
        history.count_completed()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Toplam Analiz",
            total_records,
        )

    with col2:
        st.metric(
            "Sonucu Girilmiş",
            completed_records,
        )

    records = history.list(
        limit=100
    )

    if not records:

        st.info(
            "Henüz kayıtlı Q200 analizi yok."
        )

        return

    st.subheader(
        "Kayıtlı Analizler"
    )

    rows = []

    for record in records:

        if record["settlement_recorded"]:
            status = "SETTLED"

        elif record["result_recorded"]:
            status = "RESULT RECORDED"

        else:
            status = "PENDING"

        score = "-"

        if record["result_recorded"]:

            score = (
                f"{record['home_goals']}"
                f" - "
                f"{record['away_goals']}"
            )

        rows.append(
            {
                "ID": record["id"],
                "Match": record["match_id"],
                "Created": record["created_at"],
                "Model": record["model_version"],
                "Score": score,
                "Status": status,
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------------------------------
    # RECORD SELECTION
    # -----------------------------------------------------

    record_ids = [
        record["id"]
        for record in records
    ]

    def format_history_record(value: int) -> str:
        match_id = next(
            (
                r["match_id"]
                for r in records
                if r["id"] == value
            ),
            "Unknown",
        )

        return f"{value} - {match_id}"


    selected_id = st.selectbox(
        "History kaydı seç",
        record_ids,
        format_func=format_history_record,
    )

    selected_record = history.get(
        int(selected_id)
    )

    if selected_record is None:

        st.error(
            "History kaydı bulunamadı."
        )

        return

    # -----------------------------------------------------
    # SELECTED RECORD
    # -----------------------------------------------------

    st.subheader(
        "Seçilen History Kaydı"
    )

    st.write(
        f"**Record ID:** "
        f"{selected_record['id']}"
    )

    st.write(
        f"**Match ID:** "
        f"{selected_record['match_id']}"
    )

    st.write(
        f"**Created:** "
        f"{selected_record['created_at']}"
    )

    st.write(
        f"**Model:** "
        f"{selected_record['model_version']}"
    )

    # -----------------------------------------------------
    # RESULT STATUS
    # -----------------------------------------------------

    if selected_record[
        "result_recorded"
    ]:

        st.success(
            "Maç sonucu kayıtlı: "
            f"{selected_record['home_goals']}"
            " - "
            f"{selected_record['away_goals']}"
        )

    else:

        st.warning(
            "Bu kayıt için maç sonucu henüz girilmedi."
        )

    # -----------------------------------------------------
    # SETTLEMENT STATUS
    # -----------------------------------------------------

    if selected_record[
        "settlement_recorded"
    ]:

        st.success(
            "Settlement kayıtlı."
        )

    elif selected_record[
        "result_recorded"
    ]:

        st.info(
            "Maç sonucu mevcut. Settlement çalıştırılabilir."
        )

    # -----------------------------------------------------
    # RESULT INPUT
    # -----------------------------------------------------

    st.subheader(
        "Maç Sonucu"
    )

    result_col1, result_col2 = st.columns(2)

    with result_col1:

        home_goals = st.number_input(
            "HOME Goller",
            min_value=0,
            max_value=30,
            value=(
                int(
                    selected_record[
                        "home_goals"
                    ]
                )
                if selected_record[
                    "result_recorded"
                ]
                else 0
            ),
            step=1,
            key=f"home_goals_{selected_id}",
        )

    with result_col2:

        away_goals = st.number_input(
            "AWAY Goller",
            min_value=0,
            max_value=30,
            value=(
                int(
                    selected_record[
                        "away_goals"
                    ]
                )
                if selected_record[
                    "result_recorded"
                ]
                else 0
            ),
            step=1,
            key=f"away_goals_{selected_id}",
        )

    if st.button(
        "💾 MAÇ SONUCUNU KAYDET",
        key=f"save_result_{selected_id}",
        use_container_width=True,
    ):

        try:

            success = history.record_result(
                int(selected_id),
                int(home_goals),
                int(away_goals),
            )

            if not success:

                st.error(
                    "History sonucu kaydedilemedi."
                )

            else:

                st.success(
                    "Maç sonucu başarıyla kaydedildi."
                )

                st.rerun()

        except Exception as exc:

            st.error(
                f"Sonuç kayıt hatası: {exc}"
            )

    # -----------------------------------------------------
    # SETTLEMENT
    # -----------------------------------------------------

    if selected_record[
        "result_recorded"
    ]:

        st.subheader(
            "Settlement"
        )

        if st.button(
            "⚖️ SETTLEMENT ÇALIŞTIR",
            key=f"settle_{selected_id}",
            type="primary",
            use_container_width=True,
        ):

            try:

                settlement = (
                    history.settle_record(
                        int(selected_id)
                    )
                )

                st.success(
                    "Settlement başarıyla tamamlandı."
                )

                summary = settlement.get(
                    "summary",
                    {},
                )

                settlement_cols = st.columns(6)

                with settlement_cols[0]:

                    st.metric(
                        "Bets",
                        summary.get(
                            "total_bets",
                            0,
                        ),
                    )

                with settlement_cols[1]:

                    st.metric(
                        "Wins",
                        summary.get(
                            "wins",
                            0,
                        ),
                    )

                with settlement_cols[2]:

                    st.metric(
                        "Losses",
                        summary.get(
                            "losses",
                            0,
                        ),
                    )

                with settlement_cols[3]:

                    st.metric(
                        "Voids",
                        summary.get(
                            "voids",
                            0,
                        ),
                    )

                with settlement_cols[4]:

                    st.metric(
                        "Profit",
                        _format_money(
                            summary.get(
                                "total_profit",
                                0.0,
                            )
                        ),
                    )

                with settlement_cols[5]:

                    st.metric(
                        "ROI",
                        _format_percent(
                            summary.get(
                                "roi",
                                0.0,
                            )
                        ),
                    )

                st.json(
                    settlement
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Settlement hatası: {exc}"
                )

    # -----------------------------------------------------
    # STORED SETTLEMENT
    # -----------------------------------------------------

    refreshed_record = history.get(
        int(selected_id)
    )

    if (
        refreshed_record is not None
        and refreshed_record[
            "settlement_recorded"
        ]
    ):

        st.subheader(
            "Kayıtlı Settlement"
        )

        settlement = (
            refreshed_record[
                "settlement"
            ]
        )

        if settlement is not None:

            summary = settlement.get(
                "summary",
                {},
            )

            rows = []

            for item in settlement.get(
                "selections",
                [],
            ):

                rows.append(
                    {
                        "Outcome": item.get(
                            "outcome",
                            "",
                        ),
                        "Odds": item.get(
                            "odds",
                            "",
                        ),
                        "Stake": item.get(
                            "stake",
                            0.0,
                        ),
                        "Settlement": item.get(
                            "settlement",
                            "",
                        ),
                        "Profit": item.get(
                            "profit",
                            0.0,
                        ),
                    }
                )

            if rows:

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            summary_cols = st.columns(4)

            with summary_cols[0]:

                st.metric(
                    "Toplam Stake",
                    _format_money(
                        summary.get(
                            "total_stake",
                            0.0,
                        )
                    ),
                )

            with summary_cols[1]:

                st.metric(
                    "Toplam Profit",
                    _format_money(
                        summary.get(
                            "total_profit",
                            0.0,
                        )
                    ),
                )

            with summary_cols[2]:

                st.metric(
                    "ROI",
                    _format_percent(
                        summary.get(
                            "roi",
                            0.0,
                        )
                    ),
                )

            with summary_cols[3]:

                st.metric(
                    "Hit Rate",
                    _format_percent(
                        summary.get(
                            "hit_rate",
                            0.0,
                        )
                    ),
                )

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    st.subheader(
        "History Yönetimi"
    )

    delete_confirm = st.checkbox(
        "Bu History kaydını silmek istiyorum.",
        key=f"delete_confirm_{selected_id}",
    )

    if delete_confirm:

        if st.button(
            "🗑️ SEÇİLİ KAYDI SİL",
            key=f"delete_{selected_id}",
        ):

            try:

                deleted = history.delete(
                    int(selected_id)
                )

                if deleted:

                    st.success(
                        "History kaydı silindi."
                    )

                    st.rerun()

                else:

                    st.error(
                        "History kaydı bulunamadı."
                    )

            except Exception as exc:

                st.error(
                    f"History silme hatası: {exc}"
                )


# =========================================================
# EVALUATION UI
# =========================================================

def show_evaluation_section() -> None:
    """
    History üzerinden Performance +
    Calibration + Market Evaluation gösterir.

    Bu katman salt-okunurdur.
    """

    st.header(
        "6. Evaluation Dashboard"
    )

    total_records = history.count()

    if total_records == 0:

        st.info(
            "Evaluation için önce en az bir analiz kaydı gerekir."
        )

        return

    col1, col2 = st.columns(2)

    with col1:

        starting_bankroll = st.number_input(
            "Evaluation başlangıç bankroll",
            min_value=0.0,
            value=50000.0,
            step=100.0,
            key="evaluation_bankroll",
        )

    with col2:

        bucket_count = st.number_input(
            "Calibration bucket sayısı",
            min_value=2,
            max_value=50,
            value=10,
            step=1,
            key="evaluation_bucket_count",
        )

    if st.button(
        "📊 EVALUATION OLUŞTUR",
        type="primary",
        use_container_width=True,
    ):

        try:

            evaluation = build_evaluation(
                history,
                starting_bankroll=float(
                    starting_bankroll
                ),
                bucket_count=int(
                    bucket_count
                ),
            )

            st.session_state[
                "q200_evaluation"
            ] = evaluation

        except Exception as exc:

            st.error(
                f"Evaluation hatası: {exc}"
            )

    evaluation = st.session_state.get(
        "q200_evaluation"
    )

    if evaluation is None:

        st.info(
            "Evaluation oluşturmak için butona basın."
        )

        return

    # -----------------------------------------------------
    # PERFORMANCE
    # -----------------------------------------------------

    st.subheader(
        "Performance"
    )

    performance = (
        evaluation.performance
    )

    cols = st.columns(5)

    with cols[0]:

        st.metric(
            "Analiz",
            performance.total_analysis_records,
        )

    with cols[1]:

        st.metric(
            "Completed",
            performance.completed_matches,
        )

    with cols[2]:

        st.metric(
            "Settled",
            performance.settled_matches,
        )

    with cols[3]:

        st.metric(
            "Total Bets",
            performance.total_bets,
        )

    with cols[4]:

        st.metric(
            "Wins",
            performance.wins,
        )

    cols = st.columns(5)

    with cols[0]:

        st.metric(
            "Losses",
            performance.losses,
        )

    with cols[1]:

        st.metric(
            "Voids",
            performance.voids,
        )

    with cols[2]:

        st.metric(
            "Total Stake",
            _format_money(
                performance.total_stake
            ),
        )

    with cols[3]:

        st.metric(
            "Total Profit",
            _format_money(
                performance.total_profit
            ),
        )

    with cols[4]:

        st.metric(
            "ROI",
            _format_percent(
                performance.roi
            ),
        )

    cols = st.columns(4)

    with cols[0]:

        st.metric(
            "Hit Rate",
            _format_percent(
                performance.hit_rate
            ),
        )

    with cols[1]:

        st.metric(
            "Starting Bankroll",
            _format_money(
                performance.starting_bankroll
            ),
        )

    with cols[2]:

        st.metric(
            "Ending Bankroll",
            _format_money(
                performance.ending_bankroll
            ),
        )

    with cols[3]:

        st.metric(
            "Profit",
            _format_money(
                performance.total_profit
            ),
        )

    # -----------------------------------------------------
    # CALIBRATION
    # -----------------------------------------------------

    st.subheader(
        "Calibration"
    )

    calibration = (
        evaluation.calibration
    )

    cols = st.columns(5)

    with cols[0]:

        st.metric(
            "Predictions",
            calibration.total_predictions,
        )

    with cols[1]:

        st.metric(
            "Evaluated",
            calibration.evaluated_predictions,
        )

    with cols[2]:

        st.metric(
            "Voids",
            calibration.void_predictions,
        )

    with cols[3]:

        st.metric(
            "Brier Score",
            f"{calibration.brier_score:.6f}",
        )

    with cols[4]:

        st.metric(
            "Log Loss",
            f"{calibration.log_loss:.6f}",
        )

    cols = st.columns(3)

    with cols[0]:

        st.metric(
            "Mean Probability",
            _format_percent(
                calibration.mean_predicted_probability
            ),
        )

    with cols[1]:

        st.metric(
            "Empirical Win Rate",
            _format_percent(
                calibration.empirical_win_rate
            ),
        )

    with cols[2]:

        st.metric(
            "Coverage",
            _format_percent(
                calibration.coverage
            ),
        )

    # -----------------------------------------------------
    # MARKET PERFORMANCE
    # -----------------------------------------------------

    st.subheader(
        "Market Performance"
    )

    market_rows = []

    for market_name, result in (
        evaluation.market_performance.items()
    ):

        market_rows.append(
            {
                "Market": market_name,
                "Bets": result.total_bets,
                "Wins": result.wins,
                "Losses": result.losses,
                "Voids": result.voids,
                "Stake": result.total_stake,
                "Profit": result.total_profit,
                "ROI": result.roi,
                "Hit Rate": result.hit_rate,
            }
        )

    if market_rows:

        st.dataframe(
            market_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Market performance verisi bulunamadı."
        )

    # -----------------------------------------------------
    # MARKET CALIBRATION
    # -----------------------------------------------------

    st.subheader(
        "Market Calibration"
    )

    calibration_rows = []

    for market_name, result in (
        evaluation.market_calibration.items()
    ):

        calibration_rows.append(
            {
                "Market": market_name,
                "Predictions": result.total_predictions,
                "Evaluated": result.evaluated_predictions,
                "Brier": result.brier_score,
                "Log Loss": result.log_loss,
                "Predicted": result.mean_predicted_probability,
                "Actual": result.empirical_win_rate,
                "Coverage": result.coverage,
            }
        )

    if calibration_rows:

        st.dataframe(
            calibration_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Market calibration verisi bulunamadı."
        )

    # -----------------------------------------------------
    # CALIBRATION BUCKETS
    # -----------------------------------------------------

    st.subheader(
        "Calibration Buckets"
    )

    bucket_rows = []

    for bucket in (
        evaluation.calibration_buckets
    ):

        bucket_rows.append(
            {
                "Bucket": getattr(
                    bucket,
                    "bucket",
                    "",
                ),
                "Count": getattr(
                    bucket,
                    "count",
                    0,
                ),
                "Predicted": getattr(
                    bucket,
                    "mean_predicted_probability",
                    0.0,
                ),
                "Actual": getattr(
                    bucket,
                    "empirical_win_rate",
                    0.0,
                ),
            }
        )

    if bucket_rows:

        st.dataframe(
            bucket_rows,
            use_container_width=True,
            hide_index=True,
        )

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    st.subheader(
        "Evaluation Export"
    )

    evaluation_json = evaluation_to_json(
        evaluation
    )

    evaluation_text = evaluation_to_text(
        evaluation
    )

    tab_text, tab_json = st.tabs(
        [
            "TXT",
            "JSON",
        ]
    )

    with tab_text:

        st.code(
            evaluation_text,
            language="text",
        )

        st.download_button(
            label="Evaluation TXT İndir",
            data=evaluation_text,
            file_name="q200_evaluation.txt",
            mime="text/plain",
        )

    with tab_json:

        st.code(
            evaluation_json,
            language="json",
        )

        st.download_button(
            label="Evaluation JSON İndir",
            data=evaluation_json,
            file_name="q200_evaluation.json",
            mime="application/json",
        )


# =========================================================
# HEADER
# =========================================================

st.title(
    "⚽ Q200 Football Quant Engine"
)

st.caption(
    f"{APP_VERSION} | Q200 V3.1"
)

st.markdown(
    """
### Five Source Analysis

Bu ekran aşağıdaki kaynakları tek analizde birleştirir:

- StatsHub HOME
- StatsHub AWAY
- SoccerSTATS
- PPI
- Odds

**Odds model oluşturma aşamasında kullanılmaz.**

Model oluşturulur ve LOCK edilir.

Odds yalnızca bundan sonra analiz edilir.

Analiz sonuçları kalıcı History veritabanına kaydedilebilir.
"""
)


# =========================================================
# MATCH INFORMATION
# =========================================================

st.header(
    "1. Maç Bilgileri"
)

col1, col2 = st.columns(2)

with col1:

    home_team = st.text_input(
        "HOME takım",
        placeholder="Real Betis",
    )

with col2:

    away_team = st.text_input(
        "AWAY takım",
        placeholder="Getafe",
    )

col1, col2, col3 = st.columns(3)

with col1:

    match_date = st.text_input(
        "Tarih",
        placeholder="2026-09-17",
    )

with col2:

    match_time = st.text_input(
        "Saat",
        placeholder="20:00",
    )

with col3:

    competition = st.text_input(
        "Lig",
        placeholder="Spain - LaLiga",
    )


# =========================================================
# BANKROLL / SETTINGS
# =========================================================

st.header(
    "2. Analiz Ayarları"
)

col1, col2, col3 = st.columns(3)

with col1:

    bankroll = st.number_input(
        "Bankroll",
        min_value=1.0,
        value=50000.0,
        step=100.0,
    )

with col2:

    market = st.selectbox(
        "Market",
        [
            "1X2",
        ],
    )

with col3:

    uncertainty = st.selectbox(
        "Uncertainty",
        [
            "LOW",
            "MEDIUM",
            "HIGH",
            "VERY_HIGH",
        ],
        index=1,
    )


# =========================================================
# SOURCE INPUT
# =========================================================

st.header(
    "3. Five Source Verileri"
)

st.subheader(
    "StatsHub HOME"
)

home_text = st.text_area(
    "StatsHub HOME metni",
    height=260,
    placeholder=(
        "Goals 3.05 1.70 1.35\n"
        "Expected Goals (xG) 2.92 1.50 1.41\n"
        "Total Shots 26.50 15.05 11.45\n"
        "Shots On Target 10.50 5.65 4.85"
    ),
)

st.subheader(
    "StatsHub AWAY"
)

away_text = st.text_area(
    "StatsHub AWAY metni",
    height=260,
    placeholder=(
        "Goals 1.85 0.95 0.90\n"
        "Expected Goals (xG) 1.90 0.76 1.14\n"
        "Total Shots 21.75 9.25 12.50\n"
        "Shots On Target 6.70 2.80 3.90"
    ),
)


st.subheader(
    "SoccerSTATS PDF"
)

soccerstats_file = st.file_uploader(
    "SoccerSTATS PDF yükle",
    type=["pdf"],
    key="soccerstats",
)


st.subheader(
    "PPI PDF"
)

ppi_file = st.file_uploader(
    "PPI PDF yükle",
    type=["pdf"],
    key="ppi",
)


st.subheader(
    "Odds PDF"
)

odds_file = st.file_uploader(
    "Odds PDF yükle",
    type=["pdf"],
    key="odds",
)


# =========================================================
# ANALYSIS
# =========================================================

st.header(
    "4. Q200 Analizi"
)

run_button = st.button(
    "🚀 Q200 ANALİZİNİ ÇALIŞTIR",
    type="primary",
    use_container_width=True,
)


if run_button:

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    missing = []

    if not home_team.strip():
        missing.append(
            "HOME takım"
        )

    if not away_team.strip():
        missing.append(
            "AWAY takım"
        )

    if not home_text.strip():
        missing.append(
            "StatsHub HOME"
        )

    if not away_text.strip():
        missing.append(
            "StatsHub AWAY"
        )

    if soccerstats_file is None:
        missing.append(
            "SoccerSTATS PDF"
        )

    if ppi_file is None:
        missing.append(
            "PPI PDF"
        )

    if odds_file is None:
        missing.append(
            "Odds PDF"
        )

    if missing:

        st.error(
            "Eksik girişler: "
            + ", ".join(missing)
        )

        st.stop()

    # -----------------------------------------------------
    # MATCH
    # -----------------------------------------------------

    match = MatchInfo(
        home_team=home_team.strip(),
        away_team=away_team.strip(),
        date=(
            match_date.strip()
            or None
        ),
        time=(
            match_time.strip()
            or None
        ),
        competition=(
            competition.strip()
            or None
        ),
        source="Q200-STREAMLIT",
    )

    # -----------------------------------------------------
    # TEMP FILES
    # -----------------------------------------------------

    try:

        soccerstats_path = (
            save_uploaded_file(
                soccerstats_file
            )
        )

        ppi_path = (
            save_uploaded_file(
                ppi_file
            )
        )

        odds_path = (
            save_uploaded_file(
                odds_file
            )
        )

        # -------------------------------------------------
        # STATSHUB
        # -------------------------------------------------

        with st.spinner(
            "StatsHub verileri hazırlanıyor..."
        ):

            statshub_home = (
                load_statshub_text(
                    home_text,
                    match=match,
                )
            )

            statshub_away = (
                load_statshub_text(
                    away_text,
                    match=match,
                )
            )

        # -------------------------------------------------
        # SOCCERSTATS
        # -------------------------------------------------

        with st.spinner(
            "SoccerSTATS PDF okunuyor..."
        ):

            soccerstats = (
                parse_soccerstats_pdf(
                    soccerstats_path
                )
            )

        # -------------------------------------------------
        # PPI
        # -------------------------------------------------

        with st.spinner(
            "PPI PDF okunuyor..."
        ):

            ppi = load_ppi_pdf(
                ppi_path,
                match=match,
            )

        # -------------------------------------------------
        # ODDS
        # -------------------------------------------------

        with st.spinner(
            "Odds PDF okunuyor..."
        ):

            odds = parse_odds_pdf(
                odds_path
            )

        # -------------------------------------------------
        # MATCH CHECKS
        # -------------------------------------------------

        if soccerstats.match is not None:

            if (
                soccerstats.match.home_team.casefold()
                != match.home_team.casefold()
                or
                soccerstats.match.away_team.casefold()
                != match.away_team.casefold()
            ):

                raise ValueError(
                    "SoccerSTATS maç takımları "
                    "girilen maçla eşleşmiyor."
                )

        if odds.match is not None:

            if (
                odds.match.home_team.casefold()
                != match.home_team.casefold()
                or
                odds.match.away_team.casefold()
                != match.away_team.casefold()
            ):

                raise ValueError(
                    "Odds PDF maç takımları "
                    "girilen maçla eşleşmiyor."
                )

        # -------------------------------------------------
        # FIVE SOURCE INPUT
        # -------------------------------------------------

        data = build_five_source_input(
            match=match,
            statshub_home=statshub_home,
            statshub_away=statshub_away,
            soccerstats_pdf=soccerstats_path,
            ppi_pdf=ppi_path,
            odds_pdf=odds_path,
        )

        # -------------------------------------------------
        # SOURCE STATUS
        # -------------------------------------------------

        st.success(
            "Five Source Input oluşturuldu."
        )

        status_cols = st.columns(5)

        source_names = [
            (
                "StatsHub HOME",
                data.statshub_home,
            ),
            (
                "StatsHub AWAY",
                data.statshub_away,
            ),
            (
                "SoccerSTATS",
                data.soccerstats,
            ),
            (
                "PPI",
                data.ppi,
            ),
            (
                "Odds",
                data.odds,
            ),
        ]

        for column, (
            name,
            source,
        ) in zip(
            status_cols,
            source_names,
        ):

            with column:

                if source is not None:

                    st.success(
                        name
                    )

                else:

                    st.error(
                        name
                    )

        # -------------------------------------------------
        # FINAL ANALYSIS
        # -------------------------------------------------

        with st.spinner(
            "Q200 modeli oluşturuluyor, "
            "LOCK ediliyor ve odds analiz ediliyor..."
        ):

            result = (
                run_five_source_analysis(
                    data,
                    market=market,
                    bankroll=float(
                        bankroll
                    ),
                    uncertainty=uncertainty,
                )
            )

        # -------------------------------------------------
        # LOCK CHECK
        # -------------------------------------------------

        if not result.snapshot.locked:

            raise RuntimeError(
                "Q200 modeli LOCK edilmedi."
            )

        st.session_state[
            "q200_result"
        ] = result

        st.success(
            "Q200 analizi başarıyla tamamlandı."
        )

    except Exception as exc:

        st.error(
            f"Q200 analiz hatası: {exc}"
        )


# =========================================================
# DISPLAY STORED RESULT
# =========================================================

if (
    "q200_result"
    in st.session_state
):

    st.divider()

    show_result(
        st.session_state[
            "q200_result"
        ]
    )

    # -----------------------------------------------------
    # SAVE CURRENT ANALYSIS
    # -----------------------------------------------------

    st.subheader(
        "History'ye Kaydet"
    )

    current_result = st.session_state[
        "q200_result"
    ]

    default_match_id = (
        f"{home_team.strip()} "
        f"vs "
        f"{away_team.strip()}"
    )

    history_match_id = st.text_input(
        "Match ID",
        value=default_match_id,
        key="history_match_id",
    )

    if st.button(
        "💾 ANALİZİ HISTORY'YE KAYDET",
        type="primary",
        use_container_width=True,
    ):

        try:

            record_id = history.save(
                current_result,
                history_match_id,
            )

            st.success(
                "Analiz History'ye kaydedildi. "
                f"Record ID: {record_id}"
            )

        except Exception as exc:

            st.error(
                f"History kayıt hatası: {exc}"
            )


# =========================================================
# HISTORY
# =========================================================

st.divider()

show_history_section()


# =========================================================
# EVALUATION
# =========================================================

st.divider()

show_evaluation_section()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Q200 V3.1 | Five Source | "
    "Model Lock | History | Settlement | Evaluation"
)
