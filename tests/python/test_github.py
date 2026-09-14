import base64
import json

from core import github

# ============================================================
# PETICIONES HTTP
# ============================================================

def test_github_request_with_json_response(
    monkeypatch,
):
    # Envía datos y devuelve la respuesta JSON
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            pass

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout):
        captured["request"] = req
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        github.request,
        "urlopen",
        fake_urlopen,
    )

    result = github.github_request(
        "PUT",
        "contents/test.json",
        {
            "value": "test",
        },
    )

    assert result == {
        "ok": True,
    }

    assert captured["timeout"] == 30

    assert (
        captured["request"].full_url
        == (
            "https://api.github.com/repos/"
            "Maria0696/script-station/"
            "contents/test.json"
        )
    )

    assert (
        captured["request"].get_method()
        == "PUT"
    )

    assert json.loads(
        captured["request"].data
    ) == {
        "value": "test",
    }

    headers = {
        key.lower(): value
        for key, value
        in captured[
            "request"
        ].header_items()
    }

    assert (
        headers["authorization"]
        == f"Bearer {github.GITHUB_TOKEN}"
    )

    assert (
        headers["accept"]
        == "application/vnd.github+json"
    )

    assert (
        headers["x-github-api-version"]
        == "2022-11-28"
    )

    assert (
        headers["content-type"]
        == "application/json"
    )


def test_github_request_without_body(
    monkeypatch,
):
    # Permite peticiones sin datos
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            pass

        def read(self):
            return b'{"value": 123}'

    def fake_urlopen(req, timeout):
        captured["request"] = req

        return FakeResponse()

    monkeypatch.setattr(
        github.request,
        "urlopen",
        fake_urlopen,
    )

    result = github.github_request(
        "GET",
        "actions/runs",
    )

    assert result == {
        "value": 123,
    }

    assert (
        captured["request"].data
        is None
    )


def test_github_request_without_content(
    monkeypatch,
):
    # Devuelve vacío si GitHub no envía contenido
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            pass

        def read(self):
            return b""

    monkeypatch.setattr(
        github.request,
        "urlopen",
        lambda req, timeout:
            FakeResponse(),
    )

    result = github.github_request(
        "GET",
        "actions/runs",
    )

    assert result == {}


# ============================================================
# WATCHLIST
# ============================================================

def test_get_watchlist(
    monkeypatch,
):
    # Lee y decodifica la watchlist de GitHub
    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
        },
        {
            "id": 456,
            "name": "Another Game",
        },
    ]

    encoded_content = (
        base64.b64encode(
            json.dumps(
                watchlist
            ).encode("utf-8")
        ).decode("utf-8")
    )

    captured = {}

    def fake_github_request(
        method,
        path,
        data=None,
    ):
        captured["method"] = method
        captured["path"] = path

        return {
            "content": encoded_content,
            "sha": "test-sha",
        }

    monkeypatch.setattr(
        github,
        "github_request",
        fake_github_request,
    )

    result, sha = github.get_watchlist()

    assert result == watchlist
    assert sha == "test-sha"

    assert captured["method"] == "GET"

    assert captured["path"] == (
        "contents/data/watchlist.json"
        "?ref=master"
    )


def test_save_watchlist(
    monkeypatch,
):
    # Codifica y guarda la watchlist en GitHub
    watchlist = [
        {
            "id": 123,
            "name": "Pokémon Test",
        }
    ]

    captured = {}

    def fake_github_request(
        method,
        path,
        data=None,
    ):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data

        return {}

    monkeypatch.setattr(
        github,
        "github_request",
        fake_github_request,
    )

    github.save_watchlist(
        watchlist,
        "test-sha",
    )

    assert captured["method"] == "PUT"

    assert (
        captured["path"]
        == "contents/data/watchlist.json"
    )

    assert (
        captured["data"]["message"]
        == "chore: update game watchlist"
    )

    assert (
        captured["data"]["sha"]
        == "test-sha"
    )

    assert (
        captured["data"]["branch"]
        == "master"
    )

    decoded_content = (
        base64.b64decode(
            captured[
                "data"
            ]["content"]
        ).decode("utf-8")
    )

    assert json.loads(
        decoded_content
    ) == watchlist

    assert "Pokémon Test" in (
        decoded_content
    )


# ============================================================
# WORKFLOWS
# ============================================================

def test_get_workflow_runs(
    monkeypatch,
):
    # Devuelve las ejecuciones de workflows
    workflow_runs = [
        {
            "id": 1,
            "name": "Quality Checks",
        },
        {
            "id": 2,
            "name":
                "Daily Video Game Releases",
        },
    ]

    captured = {}

    def fake_github_request(
        method,
        path,
        data=None,
    ):
        captured["method"] = method
        captured["path"] = path

        return {
            "workflow_runs":
                workflow_runs,
        }

    monkeypatch.setattr(
        github,
        "github_request",
        fake_github_request,
    )

    result = github.get_workflow_runs()

    assert result == workflow_runs

    assert captured["method"] == "GET"

    assert captured["path"] == (
        "actions/runs"
        "?branch=master"
        "&per_page=50"
    )


def test_get_workflow_runs_without_results(
    monkeypatch,
):
    # Devuelve vacío si no hay workflows
    monkeypatch.setattr(
        github,
        "github_request",
        lambda method, path: {},
    )

    result = github.get_workflow_runs()

    assert result == []
