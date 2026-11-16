import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest
import requests
from requests.adapters import HTTPAdapter

from core import igdb


def timestamp(year, month, day):
    # Crea timestamps UTC para los tests
    return int(datetime(year, month, day, tzinfo=UTC).timestamp())


class FakeResponse:
    # Respuesta mínima de requests

    def __init__(self, data, status_code=200, text=""):
        self.data = data
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = text

    def json(self):
        return self.data

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def mock_igdb_request(monkeypatch, result):
    # Sustituye igdb_request y guarda las llamadas
    calls = []

    def fake_request(endpoint, query):
        calls.append({"endpoint": endpoint, "query": query})

        return result

    monkeypatch.setattr(igdb, "igdb_request", fake_request)

    return calls


# ============================================================
# FECHAS
# ============================================================


def test_format_release_date():
    # Convierte timestamp a fecha interna
    result = igdb.format_release_date(timestamp(2026, 9, 15))

    assert result == "2026-09-15"


def test_format_release_date_without_timestamp():
    # Devuelve None si no hay timestamp
    assert igdb.format_release_date(None) is None


def test_display_release_date():
    # Convierte la fecha al formato visible
    result = igdb.display_release_date("2026-09-15")

    assert result == "15-09-2026"


def test_display_release_date_without_date():
    # Muestra texto cuando no hay fecha
    assert igdb.display_release_date(None) == "Sin fecha"


# ============================================================
# TOKEN
# ============================================================


def test_get_igdb_token(monkeypatch):
    # Pide el token de Twitch con las credenciales
    captured = {}

    def fake_post(url, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)

        return FakeResponse({"access_token": "test-token", "expires_in": 3600})

    monkeypatch.setattr(igdb.session, "post", fake_post)

    assert igdb.get_igdb_token() == "test-token"

    assert captured == {
        "url": "https://id.twitch.tv/oauth2/token",
        "params": {
            "client_id": igdb.IGDB_CLIENT_ID,
            "client_secret": igdb.IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        "timeout": 30,
    }


def test_get_igdb_token_is_reused_until_expiry(monkeypatch):
    # No pide otro token mientras el actual siga vigente
    calls = []
    now = [1000.0]

    def fake_post(url, params, timeout):
        calls.append(url)

        return FakeResponse({"access_token": f"token-{len(calls)}", "expires_in": 3600})

    monkeypatch.setattr(igdb.session, "post", fake_post)

    monkeypatch.setattr(igdb.time, "monotonic", lambda: now[0])

    assert igdb.get_igdb_token() == "token-1"

    # Dentro del plazo: mismo token
    now[0] += 3600 - igdb.TOKEN_EXPIRY_MARGIN - 1
    assert igdb.get_igdb_token() == "token-1"

    # Pasado el plazo: token nuevo
    now[0] += 2
    assert igdb.get_igdb_token() == "token-2"

    assert len(calls) == 2


def test_get_igdb_token_error(monkeypatch):
    # Un error de Twitch no deja token en caché
    monkeypatch.setattr(
        igdb.session,
        "post",
        lambda url, params, timeout: FakeResponse({}, status_code=401),
    )

    with pytest.raises(requests.HTTPError):
        igdb.get_igdb_token()

    assert igdb._token_cache["access_token"] is None


# ============================================================
# PETICIONES
# ============================================================


def test_igdb_request(monkeypatch):
    # Comprueba una petición genérica a IGDB
    captured = {}

    monkeypatch.setattr(igdb, "get_igdb_token", lambda: "test-token")

    def fake_post(url, headers, data, timeout):
        captured.update(url=url, headers=headers, data=data, timeout=timeout)

        return FakeResponse([{"id": 123, "name": "Test Game"}])

    monkeypatch.setattr(igdb.session, "post", fake_post)

    result = igdb.igdb_request("games", 'search "Pokémon";')

    assert result == [{"id": 123, "name": "Test Game"}]

    assert captured == {
        "url": "https://api.igdb.com/v4/games",
        "headers": {
            "Client-ID": igdb.IGDB_CLIENT_ID,
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
        },
        # Se envía en UTF-8
        "data": 'search "Pokémon";'.encode(),
        "timeout": 30,
    }


def test_igdb_request_error_includes_response(monkeypatch):
    # El error incluye el endpoint y la respuesta de IGDB
    monkeypatch.setattr(igdb, "get_igdb_token", lambda: "test-token")

    monkeypatch.setattr(
        igdb.session,
        "post",
        lambda url, headers, data, timeout: FakeResponse(
            {}, status_code=400, text="Syntax error"
        ),
    )

    with pytest.raises(
        requests.HTTPError, match="IGDB games failed: HTTP 400: Syntax error"
    ):
        igdb.igdb_request("games", "fields id")


# ============================================================
# REGIONES
# ============================================================


@pytest.mark.parametrize(
    ("release", "expected"),
    [
        ({"release_region": {"region": "europe"}}, True),
        ({"release_region": {"region": "Worldwide"}}, True),
        ({"release_region": {"region": "japan"}}, False),
        ({"release_region": {"region": None}}, True),
        ({"release_region": {}}, True),
        ({"release_region": 8}, True),
        ({}, True),
    ],
)
def test_is_valid_region(release, expected):
    # Solo Europa, Worldwide o sin región
    assert igdb.is_valid_region(release) is expected


# ============================================================
# BÚSQUEDA
# ============================================================


def test_search_igdb_games(monkeypatch):
    # Comprueba la búsqueda de juegos por nombre
    calls = mock_igdb_request(monkeypatch, [{"id": 123, "name": "Test Game"}])

    result = igdb.search_igdb_games('Game "Test"')

    assert result == [{"id": 123, "name": "Test Game"}]

    assert calls[0]["endpoint"] == "games"

    assert 'search "Game \\"Test\\"";' in calls[0]["query"]

    assert "limit 5;" in calls[0]["query"]


def test_search_igdb_games_escapes_backslashes(monkeypatch):
    # Escapa barras invertidas en búsquedas
    calls = mock_igdb_request(monkeypatch, [])

    igdb.search_igdb_games(r"Game\Test")

    assert r"Game\\Test" in calls[0]["query"]


# ============================================================
# JUEGOS
# ============================================================


def test_get_igdb_games(monkeypatch):
    # Indexa los juegos por ID
    calls = mock_igdb_request(
        monkeypatch, [{"id": 123, "name": "Game A"}, {"id": 456, "name": "Game B"}]
    )

    result = igdb.get_igdb_games([123, 456])

    assert result == {
        123: {"id": 123, "name": "Game A"},
        456: {"id": 456, "name": "Game B"},
    }

    assert calls[0]["endpoint"] == "games"
    assert "where id = (123,456);" in calls[0]["query"]


def test_get_igdb_games_empty(monkeypatch):
    # Sin IDs no consulta IGDB
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_igdb_games([]) == {}
    assert calls == []


def test_get_igdb_game(monkeypatch):
    # Obtiene un juego concreto por ID
    calls = mock_igdb_request(
        monkeypatch, [{"id": 123, "name": "Test Game", "platforms": [167]}]
    )

    result = igdb.get_igdb_game(123)

    assert result == {"id": 123, "name": "Test Game", "platforms": [167]}

    assert "where id = (123);" in calls[0]["query"]


def test_get_igdb_game_not_found(monkeypatch):
    # Devuelve None si el juego no existe
    mock_igdb_request(monkeypatch, [])

    assert igdb.get_igdb_game(999) is None


# ============================================================
# FECHAS POR PLATAFORMA
# ============================================================


def test_get_release_dates(monkeypatch):
    # Agrupa la primera fecha válida por juego y plataforma
    calls = mock_igdb_request(
        monkeypatch,
        [
            {
                "game": 123,
                "platform": 167,
                "date": timestamp(2026, 9, 15),
                "release_region": {"region": "europe"},
            },
            {
                # Formato expandido de IGDB
                "game": {"id": 456},
                "platform": 6,
                "date": timestamp(2026, 9, 20),
                "release_region": {"region": "worldwide"},
            },
            {
                # Fecha posterior: se descarta
                "game": 123,
                "platform": 167,
                "date": timestamp(2026, 10, 1),
            },
            {
                # Región no válida
                "game": 123,
                "platform": 6,
                "date": timestamp(2026, 9, 1),
                "release_region": {"region": "japan"},
            },
            {
                # Plataforma no soportada
                "game": 123,
                "platform": 999999,
                "date": timestamp(2026, 9, 15),
            },
            {
                # Sin fecha
                "game": 456,
                "platform": 167,
                "date": None,
            },
        ],
    )

    result = igdb.get_release_dates([123, 456])

    assert result == {123: {167: "2026-09-15"}, 456: {6: "2026-09-20"}}

    assert calls[0]["endpoint"] == "release_dates"
    assert "where game = (123,456)" in calls[0]["query"]

    assert f"platform = ({igdb.platform_filter()})" in calls[0]["query"]


def test_get_release_dates_empty(monkeypatch):
    # Sin IDs no consulta IGDB
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_release_dates([]) == {}
    assert calls == []


def test_get_platform_release_dates(monkeypatch):
    # Devuelve las fechas de un solo juego
    monkeypatch.setattr(
        igdb, "get_release_dates", lambda game_ids: {game_ids[0]: {167: "2026-09-15"}}
    )

    assert igdb.get_platform_release_dates(123) == {167: "2026-09-15"}


def test_get_platform_release_dates_without_dates(monkeypatch):
    # Devuelve vacío si el juego no tiene fechas
    monkeypatch.setattr(igdb, "get_release_dates", lambda game_ids: {})

    assert igdb.get_platform_release_dates(123) == {}


# ============================================================
# LANZAMIENTOS Y POPULARIDAD
# ============================================================


def test_get_releases_between(monkeypatch):
    # Consulta los lanzamientos del intervalo
    releases = [{"id": 1}]

    calls = mock_igdb_request(monkeypatch, releases)

    result = igdb.get_releases_between(1000, 2000)

    assert result == releases
    assert calls[0]["endpoint"] == "release_dates"

    query = calls[0]["query"]

    assert "where date >= 1000" in query
    assert "& date < 2000" in query
    assert f"platform = ({igdb.platform_filter()})" in query
    assert "game.name" in query


def test_get_popularity_primitives(monkeypatch):
    # Consulta la popularidad de varios juegos
    calls = mock_igdb_request(monkeypatch, [{"game_id": 123}])

    result = igdb.get_popularity_primitives([123, 456], [1, 2])

    assert result == [{"game_id": 123}]
    assert calls[0]["endpoint"] == "popularity_primitives"
    assert "where game_id = (123,456)" in calls[0]["query"]
    assert "popularity_type = (1,2)" in calls[0]["query"]


def test_get_popularity_primitives_empty(monkeypatch):
    # Sin juegos no consulta IGDB
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_popularity_primitives([], [1]) == []
    assert calls == []


# ============================================================
# PLATAFORMAS
# ============================================================


def test_build_platform_data(monkeypatch):
    # Ordena plataformas y añade sus fechas
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {167: "2026-09-15", 6: "2026-09-20"},
    )

    game = {"id": 123, "platforms": [6, 167]}

    result = igdb.build_platform_data(game)

    assert result == [
        {"id": 167, "label": "🔵 PS5", "release_date": "2026-09-15"},
        {"id": 6, "label": "💻 PC", "release_date": "2026-09-20"},
    ]


def test_build_platform_data_with_known_dates(monkeypatch):
    # Con fechas ya conocidas no consulta IGDB
    def fail(game_id):
        raise AssertionError("unexpected IGDB call")

    monkeypatch.setattr(igdb, "get_platform_release_dates", fail)

    result = igdb.build_platform_data({"id": 123, "platforms": [167]}, {})

    assert result == [{"id": 167, "label": "🔵 PS5", "release_date": None}]


def test_build_platform_data_adds_platform_from_release_date(monkeypatch):
    # Añade plataformas detectadas por su fecha
    monkeypatch.setattr(
        igdb, "get_platform_release_dates", lambda game_id: {167: "2026-09-15"}
    )

    game = {"id": 123, "platforms": []}

    result = igdb.build_platform_data(game)

    assert result == [{"id": 167, "label": "🔵 PS5", "release_date": "2026-09-15"}]


def test_build_platform_data_groups_meta_quest(monkeypatch):
    # Agrupa Quest 2 y Quest 3
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {471: "2026-10-01", 386: "2026-10-02"},
    )

    game = {"id": 123, "platforms": [471, 386]}

    result = igdb.build_platform_data(game)

    assert result == [
        {"id": 471, "label": "🥽 Meta Quest", "release_date": "2026-10-01"}
    ]


def test_build_platform_data_uses_second_quest_date_when_needed(monkeypatch):
    # Usa la fecha de Quest disponible
    monkeypatch.setattr(
        igdb, "get_platform_release_dates", lambda game_id: {386: "2026-10-02"}
    )

    game = {"id": 123, "platforms": [471, 386]}

    result = igdb.build_platform_data(game)

    assert result == [
        {"id": 471, "label": "🥽 Meta Quest", "release_date": "2026-10-02"}
    ]


def test_build_platform_data_without_platforms(monkeypatch):
    # Devuelve vacío si no hay plataformas
    monkeypatch.setattr(igdb, "get_platform_release_dates", lambda game_id: {})

    game = {"id": 123}

    result = igdb.build_platform_data(game)

    assert result == []


# ============================================================
# REINTENTOS
# ============================================================


def test_session_retries_temporary_errors():
    # Reintenta 429 y 5xx, también en POST, respetando Retry-After
    retry = igdb.session.get_adapter(igdb.IGDB_API_URL).max_retries

    assert retry.total == 3
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert "POST" in retry.allowed_methods
    assert retry.respect_retry_after_header is True

    # La última respuesta llega a igdb_request para incluirla en el error
    assert retry.raise_on_status is False


def test_session_retries_twitch_token_requests():
    # El token de Twitch usa la misma política
    retry = igdb.session.get_adapter(igdb.TWITCH_TOKEN_URL).max_retries

    assert retry.total == 3


class FlakyHandler(BaseHTTPRequestHandler):
    # Responde con los códigos de "statuses" en orden
    statuses: ClassVar[list[int]] = []
    calls = 0

    def do_POST(self):
        # Lee el cuerpo antes de responder para no cortar la conexión
        self.rfile.read(int(self.headers["Content-Length"]))
        type(self).calls += 1
        status = type(self).statuses.pop(0)
        body = b"[]" if status == 200 else b"Service Unavailable"

        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def flaky_server():
    # Servidor HTTP local para probar los reintentos reales
    FlakyHandler.calls = 0
    server = HTTPServer(("127.0.0.1", 0), FlakyHandler)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    )
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    server.server_close()


def local_session():
    # Misma política de reintentos, sin esperas y para http://
    retry = igdb.create_session().get_adapter("https://").max_retries
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry.new(backoff_factor=0)))

    return session


def test_session_recovers_from_temporary_error(flaky_server):
    FlakyHandler.statuses = [503, 200]

    response = local_session().post(flaky_server, data=b"fields id;", timeout=5)

    assert response.status_code == 200
    assert FlakyHandler.calls == 2


def test_igdb_request_reports_last_response_after_retries(monkeypatch, flaky_server):
    # Agotados los reintentos, el error incluye la respuesta de IGDB
    FlakyHandler.statuses = [503] * 4

    monkeypatch.setattr(igdb, "session", local_session())
    monkeypatch.setattr(igdb, "IGDB_API_URL", flaky_server)
    monkeypatch.setattr(igdb, "get_igdb_token", lambda: "test-token")

    with pytest.raises(requests.HTTPError, match="HTTP 503: Service Unavailable"):
        igdb.igdb_request("games", "fields id;")

    assert FlakyHandler.calls == 4
