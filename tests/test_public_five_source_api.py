from __future__ import annotations

import q200_engine


def test_five_source_public_api_is_exported() -> None:
    assert callable(
        q200_engine.build_five_source_input
    )

    assert callable(
        q200_engine.build_locked_model_from_five_sources
    )

    assert callable(
        q200_engine.run_five_source_analysis
    )

    assert callable(
        q200_engine.load_statshub_image
    )

    assert callable(
        q200_engine.load_statshub_text
    )

    assert callable(
        q200_engine.load_ppi_pdf
    )
