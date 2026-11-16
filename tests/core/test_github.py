import base64
import json

import pytest
import requests

from core import github


class FakeResponse:
    # Respuesta mínima de requests

    def __init__(self, data=None, status_code=200, content=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self.content = json.dumps(data).encode() if content is None else content
        self.text = self.content.decode()

    def json(self):
        return json.loads(self.content)


# ============================================================
# PETICIONES HTTP
# ============================================================


def mock_session(monkeypatch, response):
    # Sustituye la sesión HTTP y guarda la llamada
    captured = {}

    def fake_request(method, url, json, headers, timeout):
        captured.update(
            method=method, url=url, json=json, headers=headers, timeout=timeout
        )

        return response

    monkeypatch.setattr(github.session, "request", fake_request)

    return captured


def test_github_request_with_json_response(monkeypatch):
    captured = mock_session(monkeypatch, FakeResponse({"ok": True}))

    result = github.github_request("PUT", "contents/test.json", {"value": "test"})

    assert result == {"ok": True}

    assert captured == {
        "method": "PUT",
        "url": (
            "https://api.github.com/repos/Maria0696/script-station/contents/test.json"
        ),
        "json": {"value": "test"},
        "headers": {
            "Authorization": f"Bearer {github.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        "timeout": 30,
    }


def test_github_request_without_body(monkeypatch):
    captured = mock_session(monkeypatch, FakeResponse({"value": 123}))

    result = github.github_request("GET", "actions/runs")

    assert result == {"value": 123}

    assert captured["json"] is None


def test_github_request_without_content(monkeypatch):
    # Por ejemplo, el 204 de workflow_dispatch
    mock_session(monkeypatch, FakeResponse(status_code=204, content=b""))

    assert github.github_request("POST", "actions/workflows/x.yml/dispatches") == {}


def test_github_request_error_includes_response(monkeypatch):
    mock_session(monkeypatch, FakeResponse({"message": "Not Found"}, status_code=404))

    with pytest.raises(
        requests.HTTPError, match="GitHub GET actions/runs failed: HTTP 404"
    ):
        github.github_request("GET", "actions/runs")


def test_session_retries_only_safe_methods():
    # Lanzar workflows (POST) no se repite: podría duplicarlos
    retry = github.session.get_adapter("https://api.github.com").max_retries

    assert set(retry.allowed_methods) == {"GET", "PUT"}


# ============================================================
# WATCHLIST
# ============================================================


def test_get_watchlist(monkeypatch):
    watchlist = [{"id": 123, "name": "Test Game"}, {"id": 456, "name": "Another Game"}]

    encoded_content = base64.b64encode(json.dumps(watchlist).encode("utf-8")).decode(
        "utf-8"
    )

    captured = {}

    def fake_github_request(method, path, data=None):
        captured["method"] = method

        captured["path"] = path

        return {"content": encoded_content, "sha": "test-sha"}

    monkeypatch.setattr(github, "github_request", fake_github_request)

    result, sha = github.get_watchlist()

    assert result == watchlist

    assert sha == ("test-sha")

    assert captured["method"] == "GET"

    assert captured["path"] == ("contents/data/watchlist.json?ref=master")


def test_save_watchlist(monkeypatch):
    watchlist = [{"id": 123, "name": "Pokémon Test"}]

    captured = {}

    def fake_github_request(method, path, data=None):
        captured["method"] = method

        captured["path"] = path

        captured["data"] = data

        return {}

    monkeypatch.setattr(github, "github_request", fake_github_request)

    github.save_watchlist(watchlist, "test-sha")

    assert captured["method"] == "PUT"

    assert captured["path"] == ("contents/data/watchlist.json")

    assert captured["data"]["message"] == ("chore: update game watchlist")

    assert captured["data"]["sha"] == "test-sha"

    assert captured["data"]["branch"] == "master"

    decoded_content = base64.b64decode(captured["data"]["content"]).decode("utf-8")

    assert json.loads(decoded_content) == watchlist

    assert "Pokémon Test" in decoded_content

    assert decoded_content.endswith("\n")


def test_save_watchlist_with_custom_message(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        github, "github_request", lambda method, path, data: captured.update(data)
    )

    github.save_watchlist([], "test-sha", message="chore: custom")

    assert captured["message"] == "chore: custom"


# ============================================================
# WORKFLOWS
# ============================================================


def test_dispatch_workflow(monkeypatch):
    captured = {}

    def fake_request(method, path, data=None):
        captured["method"] = method

        captured["path"] = path

        captured["data"] = data

        return {}

    monkeypatch.setattr(github, "github_request", fake_request)

    result = github.dispatch_workflow("watchlist.yml")

    assert result == {}

    assert captured == {
        "method": "POST",
        "path": ("actions/workflows/watchlist.yml/dispatches"),
        "data": {"ref": "master"},
    }


def test_get_workflow_runs(monkeypatch):
    workflow_runs = [
        {"id": 1, "name": "Quality Checks"},
        {"id": 2, "name": ("Daily Video Game Releases")},
    ]

    captured = {}

    def fake_github_request(method, path, data=None):
        captured["method"] = method

        captured["path"] = path

        return {"workflow_runs": workflow_runs}

    monkeypatch.setattr(github, "github_request", fake_github_request)

    result = github.get_workflow_runs()

    assert result == (workflow_runs)

    assert captured["method"] == "GET"

    assert captured["path"] == ("actions/runs?branch=master&per_page=50")


def test_get_workflow_runs_without_results(monkeypatch):
    monkeypatch.setattr(github, "github_request", lambda method, path: {})

    result = github.get_workflow_runs()

    assert result == []


def test_rerun_failed_workflow_run(monkeypatch):
    captured = {}

    def fake_request(method, path, data=None):
        captured["method"] = method

        captured["path"] = path

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(github, "github_request", fake_request)

    result = github.rerun_failed_workflow_run(123)

    assert result == {"ok": True}

    assert captured["method"] == "POST"

    assert captured["path"] == ("actions/runs/123/rerun-failed-jobs")

    assert captured["data"] is None


# ============================================================
# ACTUALIZAR LA WATCHLIST
# ============================================================


def http_error(code):
    return requests.HTTPError(
        f"HTTP {code}", response=FakeResponse(status_code=code, content=b"")
    )


def mock_storage(monkeypatch, versions, save_errors=()):
    # get_watchlist devuelve cada versión por turno; save_watchlist
    # lanza los errores indicados en orden y registra lo guardado
    reads = iter(versions)
    errors = list(save_errors)
    saves = []

    monkeypatch.setattr(github, "get_watchlist", lambda: next(reads))

    def fake_save(watchlist, sha, message):
        if errors:
            raise errors.pop(0)

        saves.append((list(watchlist), sha, message))

    monkeypatch.setattr(github, "save_watchlist", fake_save)

    return saves


def add_game(game_id):
    def change(watchlist):
        watchlist.append(game_id)

        return game_id, True

    return change


def test_update_watchlist_saves_change(monkeypatch):
    saves = mock_storage(monkeypatch, [([1], "sha-1")])

    result = github.update_watchlist(add_game(2), message="chore: test")

    assert result == 2
    assert saves == [([1, 2], "sha-1", "chore: test")]


def test_update_watchlist_without_change(monkeypatch):
    # Sin cambios no hay commit
    saves = mock_storage(monkeypatch, [([1], "sha-1")])

    result = github.update_watchlist(lambda watchlist: ("same", False))

    assert result == "same"
    assert saves == []


def test_update_watchlist_retries_conflict(monkeypatch):
    # Otro proceso guardó entretanto: se repite sobre la versión nueva
    saves = mock_storage(
        monkeypatch, [([1], "sha-1"), ([1, 3], "sha-2")], save_errors=[http_error(409)]
    )

    github.update_watchlist(add_game(2))

    # No se pierde el juego 3 que guardó el otro proceso
    assert saves == [([1, 3, 2], "sha-2", "chore: update game watchlist")]


def test_update_watchlist_gives_up_after_second_conflict(monkeypatch):
    mock_storage(
        monkeypatch,
        [([1], "sha-1"), ([1], "sha-2")],
        save_errors=[http_error(409), http_error(409)],
    )

    with pytest.raises(requests.HTTPError):
        github.update_watchlist(add_game(2))


def test_update_watchlist_does_not_retry_other_errors(monkeypatch):
    mock_storage(monkeypatch, [([1], "sha-1")], save_errors=[http_error(422)])

    with pytest.raises(requests.HTTPError):
        github.update_watchlist(add_game(2))
