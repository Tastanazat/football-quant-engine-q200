from __future__ import annotations

import importlib


def test_streamlit_app_imports() -> None:
    module = importlib.import_module(
        "streamlit_app"
    )

    assert module.APP_VERSION == (
        "Q200-STREAMLIT-V1"
    )


def test_streamlit_app_version_is_declared() -> None:
    module = importlib.import_module(
        "streamlit_app"
    )

    assert isinstance(
        module.APP_VERSION,
        str,
    )

    assert module.APP_VERSION
