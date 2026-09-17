from __future__ import annotations

from pathlib import Path

from q200_engine.ingestion.canonical_adapter import (
    validated_canonical_to_team_stats,
)
from q200_engine.ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)
from q200_engine.ingestion.source_mapper import map_sources
from q200_engine.ingestion.validated_pipeline import map_and_validate


PDF_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "soccerstats"
    / "WEB_1789630115.pdf"
)


def test_real_soccerstats_pdf_to_canonical_to_team_stats() -> None:
    soccerstats = parse_soccerstats_pdf(PDF_PATH)

    assert soccerstats.match.home_team == "Real Betis"
    assert soccerstats.match.away_team == "Getafe"

    assert soccerstats.goals.home_gf_per_match == 1.00
    assert soccerstats.goals.home_ga_per_match == 0.00
    assert soccerstats.goals.away_gf_per_match == 0.00
    assert soccerstats.goals.away_ga_per_match == 2.00

    canonical = map_sources(soccerstats=soccerstats)

    assert canonical.canonical_values["home_gf_per_match"] == 1.00
    assert canonical.canonical_values["home_ga_per_match"] == 0.00
    assert canonical.canonical_values["away_gf_per_match"] == 0.00
    assert canonical.canonical_values["away_ga_per_match"] == 2.00

    assert canonical.source_trace["home_gf_per_match"] == "SoccerSTATS"
    assert canonical.source_trace["away_gf_per_match"] == "SoccerSTATS"

    validated = map_and_validate(
        soccerstats=soccerstats,
    )

    assert validated.valid is True
    assert validated.validation.issues == []

    stats = validated_canonical_to_team_stats(validated)

    assert stats.home_gf == 1.00
    assert stats.home_ga == 0.00
    assert stats.away_gf == 0.00
    assert stats.away_ga == 2.00
