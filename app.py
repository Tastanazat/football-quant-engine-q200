"""
Q200 Engine - Streamlit Application

Q200 V3.1

Five Source User Interface

Akış:

StatsHub HOME
StatsHub AWAY
SoccerSTATS PDF
PPI PDF
Odds PDF
        ↓
StatsHub OCR / Review
        ↓
FiveSourceMatchInput
        ↓
Five Source Pipeline
        ↓
MODEL LOCK
        ↓
Odds Analysis
        ↓
Q200 Report
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from q200_engine.data_review import (
    approve_review,
)
from q200_engine.five_source_loader import (
    build_five_source_input,
)
from q200_engine.five_source_pipeline import (
    run_five_source_analysis,
)
from q200_engine.ingestion.models import (
    MatchInfo,
)
from q200_engine.report import (
    build_report,
    report_to_text,
)
from q200_engine.statshub_ocr import (
    create_statshub_review,
)
from q200_engine.statshub_review_mapper import (
    review_to_statshub_data,
)


APP_VERSION = "Q200-STREAMLIT-V1"


st.set_page_config(
    page_title="Q200 Football Quant Engine",
    page_icon="⚽",
    layout="wide",
)


st.title("⚽ Q200 Football Quant Engine")
st.caption(
    f"Q200 V3.1 • {APP_VERSION}"
)


# =========================================================
# SESSION STATE
# =========================================================

if "home_review" not in st.session_state:
    st.session_state.home_review = None

if "away_review" not in st.session_state:
    st.session_state.away_review = None

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# =========================================================
# MATCH INFORMATION
# =========================================================

st.header("1. Maç Bilgileri")

col1, col2 = st.columns(2)

with col1:
    home_team = st.text_input(
        "HOME takım",
        value="Real Betis",
    )

with col2:
    away_team = st.text_input(
        "AWAY takım",
        value="Getafe",
    )

col1, col2, col3 = st.columns(3)

with col1:
    match_date = st.text_input(
        "Tarih",
        value="2026-09-17",
    )

with col2:
    match_time = st.text_input(
        "Saat",
        value="20:00",
    )

with col3:
    competition = st.text_input(
        "Lig",
        value="Spain - LaLiga",
    )


match = MatchInfo(
    home_team=home_team.strip(),
    away_team=away_team.strip(),
    date=match_date.strip() or None,
    time=match_time.strip() or None,
    competition=competition.strip() or None,
    source="Q200",
)


# =========================================================
# SOURCE FILES
# =========================================================

st.header("2. Five Source Dosyaları")

col1, col2 = st.columns(2)

with col1:
    home_image = st.file_uploader(
        "StatsHub HOME",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        key="home_image",
    )

with col2:
    away_image = st.file_uploader(
        "StatsHub AWAY",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        key="away_image",
    )

col1, col2, col3 = st.columns(3)

with col1:
    soccerstats_pdf = st.file_uploader(
        "SoccerSTATS PDF",
        type=["pdf"],
        key="soccerstats_pdf",
    )

with col2:
    ppi_pdf = st.file_uploader(
        "PPI PDF",
        type=["pdf"],
        key="ppi_pdf",
    )

with col3:
    odds_pdf = st.file_uploader(
        "Odds PDF",
        type=["pdf"],
        key="odds_pdf",
    )


# =========================================================
# OCR HELPER
# =========================================================

def save_uploaded_file(
    uploaded_file,
) -> Path:
    """
    Streamlit upload nesnesini geçici dosyaya kaydeder.
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


# =========================================================
# STATSHUB REVIEW
# =========================================================

st.header("3. StatsHub OCR / Review")

home_ocr_text = st.text_area(
    "StatsHub HOME OCR metni",
    height=180,
    placeholder=(
        "OCR metnini buraya yapıştırabilirsin. "
        "Boş bırakırsan sistem görüntüden OCR "
        "çalıştırmayı dener."
    ),
)

away_ocr_text = st.text_area(
    "StatsHub AWAY OCR metni",
    height=180,
    placeholder=(
        "OCR metnini buraya yapıştırabilirsin."
    ),
)


if st.button(
    "StatsHub Verilerini Oku",
    type="secondary",
):

    if home_image is None:
        st.error(
            "StatsHub HOME görüntüsü yüklenmedi."
        )

    elif away_image is None:
        st.error(
            "StatsHub AWAY görüntüsü yüklenmedi."
        )

    else:

        try:

            from q200_engine.statshub_ocr import (
                create_statshub_review,
            )

            home_path = save_uploaded_file(
                home_image
            )

            away_path = save_uploaded_file(
                away_image
            )

            st.session_state.home_review = (
                create_statshub_review(
                    home_path,
                    ocr_text=(
                        home_ocr_text
                        if home_ocr_text.strip()
                        else None
                    ),
                )
            )

            st.session_state.away_review = (
                create_statshub_review(
                    away_path,
                    ocr_text=(
                        away_ocr_text
                        if away_ocr_text.strip()
                        else None
                    ),
                )
            )

            st.success(
                "StatsHub verileri okundu. "
                "Şimdi kontrol edip onayla."
            )

        except Exception as exc:

            st.error(
                f"StatsHub okuma hatası: {exc}"
            )


# =========================================================
# REVIEW DISPLAY
# =========================================================

def display_review(
    title: str,
    review,
) -> bool:

    st.subheader(title)

    if review is None:
        st.info(
            "Henüz veri okunmadı."
        )
        return False

    st.write(
        f"Alan sayısı: "
        f"{review.field_count}"
    )

    st.write(
        f"Otomatik alan: "
        f"{review.auto_field_count}"
    )

    st.write(
        f"Manuel alan: "
        f"{review.manual_field_count}"
    )

    rows = []

    for name, field in review.fields.items():

        rows.append(
            {
                "field": name,
                "raw_value": field.raw_value,
                "value": field.value,
                "status": field.status,
                "confidence": field.confidence,
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
    )

    approved = st.checkbox(
        f"{title} verilerini onaylıyorum",
        key=f"approve_{title}",
    )

    if approved:

        try:

            approve_review(
                review
            )

            st.success(
                f"{title} onaylandı."
            )

            return True

        except Exception as exc:

            st.error(
                f"Onay hatası: {exc}"
            )

    return False


home_approved = display_review(
    "StatsHub HOME Review",
    st.session_state.home_review,
)

away_approved = display_review(
    "StatsHub AWAY Review",
    st.session_state.away_review,
)


# =========================================================
# ANALYSIS SETTINGS
# =========================================================

st.header("4. Q200 Analiz Ayarları")

col1, col2, col3 = st.columns(3)

with col1:
    bankroll = st.number_input(
        "Bankroll",
        min_value=1.0,
        value=50000.0,
        step=1000.0,
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
# FULL ANALYSIS
# =========================================================

st.header("5. Q200 Analizi")


can_run = (
    st.session_state.home_review is not None
    and st.session_state.away_review is not None
    and home_approved
    and away_approved
    and soccerstats_pdf is not None
    and ppi_pdf is not None
    and odds_pdf is not None
)


if not can_run:

    st.warning(
        "Analizi çalıştırmak için beş kaynak "
        "ve iki StatsHub Review onayı gereklidir."
    )


if st.button(
    "🚀 Q200 ANALİZİNİ ÇALIŞTIR",
    type="primary",
    disabled=not can_run,
):

    try:

        home_data = (
            review_to_statshub_data(
                st.session_state.home_review,
                match=match,
            )
        )

        away_data = (
            review_to_statshub_data(
                st.session_state.away_review,
                match=match,
            )
        )

        soccerstats_path = (
            save_uploaded_file(
                soccerstats_pdf
            )
        )

        ppi_path = (
            save_uploaded_file(
                ppi_pdf
            )
        )

        odds_path = (
            save_uploaded_file(
                odds_pdf
            )
        )

        data = build_five_source_input(
            match=match,
            statshub_home=home_data,
            statshub_away=away_data,
            soccerstats_pdf=soccerstats_path,
            ppi_pdf=ppi_path,
            odds_pdf=odds_path,
        )

        result = run_five_source_analysis(
            data,
            market=market,
            bankroll=float(bankroll),
            uncertainty=uncertainty,
        )

        st.session_state.analysis_result = result

        st.success(
            "Q200 analizi başarıyla tamamlandı."
        )

    except Exception as exc:

        st.session_state.analysis_result = None

        st.error(
            f"Q200 analiz hatası: {exc}"
        )


# =========================================================
# RESULT
# =========================================================

result = (
    st.session_state.analysis_result
)


if result is not None:

    st.header("6. Q200 Sonucu")

    snapshot = result.snapshot

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Lambda HOME",
            f"{snapshot.lambda_home:.6f}",
        )

    with col2:
        st.metric(
            "Lambda AWAY",
            f"{snapshot.lambda_away:.6f}",
        )

    with col3:
        st.metric(
            "Model",
            snapshot.model_version,
        )

    if snapshot.locked:

        st.success(
            "🔒 MODEL LOCK AKTİF"
        )

    else:

        st.error(
            "MODEL LOCK AKTİF DEĞİL"
        )

    st.subheader(
        "Model Probabilities"
    )

    st.json(
        dict(
            snapshot.probabilities
        )
    )

    st.subheader(
        "No-Vig Probabilities"
    )

    st.json(
        dict(
            result.no_vig_probabilities
        )
    )

    st.subheader(
        "Fair Odds"
    )

    st.json(
        dict(
            result.fair_odds
        )
    )

    st.subheader(
        "Baseline EV"
    )

    st.json(
        dict(
            result.ev
        )
    )

    st.subheader(
        "Pessimistic Probabilities"
    )

    st.json(
        dict(
            result.pessimistic_probabilities
        )
    )

    st.subheader(
        "Pessimistic EV"
    )

    st.json(
        dict(
            result.pessimistic_ev
        )
    )

    st.subheader(
        "Final Selections"
    )

    st.json(
        list(
            result.selections
        )
    )

    st.subheader(
        "Q200 Text Report"
    )

    st.code(
        report_to_text(result),
        language="text",
    )

    st.subheader(
        "Q200 JSON Report"
    )

    st.code(
        json.dumps(
            build_report(result),
            ensure_ascii=False,
            indent=2,
        ),
        language="json",
    )
