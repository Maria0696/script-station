import pytest
import requests

from scripts import smoke_test

EXPECTED = {
    ("GET", "/api/telegram"): 200,
    ("GET", "/api/heimdall"): 200,
    ("POST", "/api/telegram"): 401,
    ("POST", "/api/heimdall"): 401,
    ("GET", "/api/cron"): 401,
}


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def mock_api(monkeypatch, statuses=None):
    calls = []
    overrides = statuses or {}

    def fake_request(method, url, json, timeout):
        path = url.removeprefix("https://example.test")
        calls.append((method, path))
        result = overrides.get((method, path), EXPECTED[(method, path)])

        if isinstance(result, Exception):
            raise result

        return FakeResponse(result)

    monkeypatch.setattr(smoke_test.requests, "request", fake_request)
    monkeypatch.setattr(smoke_test.time, "sleep", lambda seconds: None)

    return calls


def test_run_checks_all_ok(monkeypatch):
    calls = mock_api(monkeypatch)

    assert smoke_test.run_checks("https://example.test") == []
    assert calls == list(EXPECTED)


def test_run_checks_reports_failures(monkeypatch):
    mock_api(
        monkeypatch,
        {
            ("POST", "/api/telegram"): 200,
            ("GET", "/api/heimdall"): requests.ConnectionError("down"),
        },
    )

    assert smoke_test.run_checks("https://example.test") == [
        "GET /api/heimdall: expected 200, got ConnectionError",
        "POST /api/telegram: expected 401, got 200",
    ]


def test_smoke_test_retries_until_ok(monkeypatch):
    results = iter([["GET /api/cron: expected 401, got 404"], []])

    monkeypatch.setattr(smoke_test, "run_checks", lambda base_url: next(results))
    monkeypatch.setattr(smoke_test.time, "sleep", lambda seconds: None)

    assert smoke_test.smoke_test("https://example.test") == []


def test_smoke_test_gives_up(monkeypatch, caplog):
    calls = mock_api(monkeypatch, {("GET", "/api/cron"): 500})

    failures = smoke_test.smoke_test("https://example.test")

    assert failures == ["GET /api/cron: expected 401, got 500"]
    assert len(calls) == len(EXPECTED) * smoke_test.ATTEMPTS
    assert "attempt 3/3 failed" in caplog.text


def test_main_fails_workflow(monkeypatch):
    monkeypatch.setattr(smoke_test, "smoke_test", lambda: ["broken"])

    with pytest.raises(SystemExit) as error:
        smoke_test.main()

    assert error.value.code == 1


def test_main_passes(monkeypatch):
    monkeypatch.setattr(smoke_test, "smoke_test", list)

    assert smoke_test.main() is None
