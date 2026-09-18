"""
Q200 Engine - Streamlit Application

Q200 V3.1

Kullanıcı arayüzü.

Akış:

Maç Bilgileri
        ↓
StatsHub HOME
StatsHub AWAY
        ↓
SoccerSTATS PDF
PPI PDF
Odds PDF
        ↓
Data Review
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


APP_VERSION = "Q200-STREAMLIT-V1"


st.set_page_config(
    page_title="Q200 Football Quant Engine",
    page_icon="⚽",
    layout="wide",
)


# =========================================================
# HELPERS
# =========================================================


def save_uploaded_file(
    uploaded_file,
) -> Path:
    """
    Streamlit UploadedFile nesnesini geçici dosyaya yazar.
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
    # FAIR ODDS
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
