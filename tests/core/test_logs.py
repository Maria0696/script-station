import logging

import pytest

from core import logs


@pytest.mark.parametrize(
    ("debug", "level"),
    [("true", logging.DEBUG), ("TRUE", logging.DEBUG), ("false", logging.INFO)],
)
def test_configure_logging(monkeypatch, debug, level):
    captured = {}

    monkeypatch.setenv("DEBUG", debug)
    monkeypatch.setattr(
        logs.logging, "basicConfig", lambda **kwargs: captured.update(kwargs)
    )

    logs.configure_logging()

    assert captured["level"] == level
    assert "%(message)s" in captured["format"]


def test_configure_logging_defaults_to_info(monkeypatch):
    captured = {}

    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.setattr(
        logs.logging, "basicConfig", lambda **kwargs: captured.update(kwargs)
    )

    logs.configure_logging()

    assert captured["level"] == logging.INFO
