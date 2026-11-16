import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest
import requests
from requests.adapters import HTTPAdapter

from core import igdb


def timestamp(year, month, day):
    return int(datetime(year, month, day, tzinfo=UTC).timestamp())


class FakeResponse:
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
    calls = []

    def fake_request(endpoint, query):
        calls.append({"endpoint": endpoint, "query": query})

        return result

    monkeypatch.setattr(igdb, "igdb_request", fake_request)

    return calls


def test_format_release_date():
    result = igdb.format_release_date(timestamp(2026, 9, 15))

    assert result == "2026-09-15"


def test_format_release_date_without_timestamp():
    assert igdb.format_release_date(None) is None


def test_display_release_date():
    result = igdb.display_release_date("2026-09-15")

    assert result == "15-09-2026"


def test_display_release_date_without_date():
    assert igdb.display_release_date(None) == "Sin fecha"


def test_get_igdb_token(monkeypatch):
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
    # Un error de Twitch no deja token en caché ni muestra el secreto,
    # que va en la URL de la petición
    monkeypatch.setattr(
        igdb.session,
        "post",
        lambda url, params, timeout: FakeResponse(
            {}, status_code=401, text="invalid client secret"
        ),
    )

    with pytest.raises(requests.HTTPError) as error:
        igdb.get_igdb_token()

    assert "Twitch token failed: HTTP 401" in str(error.value)
    assert igdb.IGDB_CLIENT_SECRET not in str(error.value)
    assert igdb._token_cache["access_token"] is None


def test_igdb_request(monkeypatch):
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
    assert igdb.is_valid_region(release) is expected


def test_search_igdb_games(monkeypatch):
    calls = mock_igdb_request(
        monkeypatch,
        [
            {"id": 1, "name": "Old", "first_release_date": 846115200},
            {"id": 2, "name": "Upcoming"},
            {"id": 3, "name": "New", "first_release_date": 1802390400},
        ],
    )

    result = igdb.search_igdb_games('Game "Test"')

    # Sin fecha primero, después del más reciente al más antiguo
    assert [game["id"] for game in result] == [2, 3, 1]

    query = calls[0]["query"]

    assert calls[0]["endpoint"] == "games"
    assert 'search "Game \\"Test\\"";' in query
    assert "where game_type = (0, 4, 8, 9, 10);" in query
    assert "platforms" in query
    assert "limit 10;" in query


def test_search_igdb_games_escapes_backslashes(monkeypatch):
    calls = mock_igdb_request(monkeypatch, [])

    igdb.search_igdb_games(r"Game\Test")

    assert r"Game\\Test" in calls[0]["query"]


def test_get_igdb_games(monkeypatch):
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
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_igdb_games([]) == {}
    assert calls == []


def test_get_igdb_game(monkeypatch):
    calls = mock_igdb_request(
        monkeypatch, [{"id": 123, "name": "Test Game", "platforms": [167]}]
    )

    result = igdb.get_igdb_game(123)

    assert result == {"id": 123, "name": "Test Game", "platforms": [167]}

    assert "where id = (123);" in calls[0]["query"]


def test_get_igdb_game_not_found(monkeypatch):
    mock_igdb_request(monkeypatch, [])

    assert igdb.get_igdb_game(999) is None


def test_get_release_dates(monkeypatch):
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

    assert result == {
        123: {167: {"date": "2026-09-15", "precision": "day"}},
        456: {6: {"date": "2026-09-20", "precision": "day"}},
    }

    assert calls[0]["endpoint"] == "release_dates"
    assert "where game = (123,456)" in calls[0]["query"]

    assert f"platform = ({igdb.platform_filter()})" in calls[0]["query"]


def test_get_release_dates_empty(monkeypatch):
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_release_dates([]) == {}
    assert calls == []


def test_get_platform_release_dates(monkeypatch):
    monkeypatch.setattr(
        igdb,
        "get_release_dates",
        lambda game_ids: {
            game_ids[0]: {167: {"date": "2026-09-15", "precision": "day"}}
        },
    )

    assert igdb.get_platform_release_dates(123) == {
        167: {"date": "2026-09-15", "precision": "day"}
    }


def test_get_platform_release_dates_without_dates(monkeypatch):
    monkeypatch.setattr(igdb, "get_release_dates", lambda game_ids: {})

    assert igdb.get_platform_release_dates(123) == {}


def test_get_releases_between(monkeypatch):
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
    calls = mock_igdb_request(monkeypatch, [{"game_id": 123}])

    result = igdb.get_popularity_primitives([123, 456], [1, 2])

    assert result == [{"game_id": 123}]
    assert calls[0]["endpoint"] == "popularity_primitives"
    assert "where game_id = (123,456)" in calls[0]["query"]
    assert "popularity_type = (1,2)" in calls[0]["query"]


def test_get_popularity_primitives_empty(monkeypatch):
    calls = mock_igdb_request(monkeypatch, [])

    assert igdb.get_popularity_primitives([], [1]) == []
    assert calls == []


def test_build_platform_data(monkeypatch):
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            167: {"date": "2026-09-15", "precision": "day"},
            6: {"date": "2026-09-20", "precision": "day"},
        },
    )

    game = {"id": 123, "platforms": [6, 167]}

    result = igdb.build_platform_data(game)

    assert result == [
        {
            "id": 167,
            "label": "🔵 PS5",
            "release_date": "2026-09-15",
            "date_precision": "day",
        },
        {
            "id": 6,
            "label": "💻 PC",
            "release_date": "2026-09-20",
            "date_precision": "day",
        },
    ]


def test_build_platform_data_with_known_dates(monkeypatch):
    def fail(game_id):
        raise AssertionError("unexpected IGDB call")

    monkeypatch.setattr(igdb, "get_platform_release_dates", fail)

    result = igdb.build_platform_data({"id": 123, "platforms": [167]}, {})

    assert result == [
        {"id": 167, "label": "🔵 PS5", "release_date": None, "date_precision": None}
    ]


def test_build_platform_data_adds_platform_from_release_date(monkeypatch):
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {167: {"date": "2026-09-15", "precision": "day"}},
    )

    game = {"id": 123, "platforms": []}

    result = igdb.build_platform_data(game)

    assert result == [
        {
            "id": 167,
            "label": "🔵 PS5",
            "release_date": "2026-09-15",
            "date_precision": "day",
        }
    ]


def test_build_platform_data_groups_meta_quest(monkeypatch):
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            471: {"date": "2026-10-01", "precision": "day"},
            386: {"date": "2026-10-02", "precision": "day"},
        },
    )

    game = {"id": 123, "platforms": [471, 386]}

    result = igdb.build_platform_data(game)

    assert result == [
        {
            "id": 471,
            "label": "🥽 Meta Quest",
            "release_date": "2026-10-01",
            "date_precision": "day",
        }
    ]


def test_build_platform_data_uses_second_quest_date_when_needed(monkeypatch):
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {386: {"date": "2026-10-02", "precision": "day"}},
    )

    game = {"id": 123, "platforms": [471, 386]}

    result = igdb.build_platform_data(game)

    assert result == [
        {
            "id": 471,
            "label": "🥽 Meta Quest",
            "release_date": "2026-10-02",
            "date_precision": "day",
        }
    ]


def test_build_platform_data_without_platforms(monkeypatch):
    monkeypatch.setattr(igdb, "get_platform_release_dates", lambda game_id: {})

    game = {"id": 123}

    result = igdb.build_platform_data(game)

    assert result == []


def test_session_retries_temporary_errors():
    retry = igdb.session.get_adapter(igdb.IGDB_API_URL).max_retries

    assert retry.total == 3
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert "POST" in retry.allowed_methods
    assert retry.respect_retry_after_header is True

    # La última respuesta llega a igdb_request para incluirla en el error
    assert retry.raise_on_status is False


def test_session_retries_twitch_token_requests():
    retry = igdb.session.get_adapter(igdb.TWITCH_TOKEN_URL).max_retries

    assert retry.total == 3


class FlakyHandler(BaseHTTPRequestHandler):
    statuses: ClassVar[list[int]] = []
    calls = 0

    def do_POST(self):
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
    retry = igdb.create_session(methods={"POST"}).get_adapter("https://").max_retries
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry.new(backoff_factor=0)))

    return session


def test_session_recovers_from_temporary_error(flaky_server):
    FlakyHandler.statuses = [503, 200]

    response = local_session().post(flaky_server, data=b"fields id;", timeout=5)

    assert response.status_code == 200
    assert FlakyHandler.calls == 2


def test_igdb_request_reports_last_response_after_retries(monkeypatch, flaky_server):
    FlakyHandler.statuses = [503] * 4

    monkeypatch.setattr(igdb, "session", local_session())
    monkeypatch.setattr(igdb, "IGDB_API_URL", flaky_server)
    monkeypatch.setattr(igdb, "get_igdb_token", lambda: "test-token")

    with pytest.raises(requests.HTTPError, match="HTTP 503: Service Unavailable"):
        igdb.igdb_request("games", "fields id;")

    assert FlakyHandler.calls == 4


def test_get_release_dates_reads_precision(monkeypatch):
    mock_igdb_request(
        monkeypatch,
        [
            {
                "game": 1,
                "platform": 167,
                "date": timestamp(2027, 12, 31),
                "date_format": {"format": "YYYY"},
            },
            {
                "game": 2,
                "platform": 167,
                "date": timestamp(2027, 3, 31),
                "date_format": {"format": "YYYYQ1"},
            },
            {
                "game": 3,
                "platform": 167,
                "date": timestamp(2027, 5, 31),
                "date_format": {"format": "YYYYMM"},
            },
            {
                "game": 4,
                "platform": 167,
                "date": timestamp(2027, 12, 31),
                "date_format": {"format": "TBD"},
            },
        ],
    )

    result = igdb.get_release_dates([1, 2, 3, 4])

    assert result == {
        1: {167: {"date": "2027-12-31", "precision": "year"}},
        2: {167: {"date": "2027-03-31", "precision": "quarter"}},
        3: {167: {"date": "2027-05-31", "precision": "month"}},
    }


@pytest.mark.parametrize(
    ("release", "expected"),
    [
        ({"date_format": {"format": "YYYYMMDD"}}, "day"),
        ({"date_format": {"format": "YYYYMM"}}, "month"),
        ({"date_format": {"format": "YYYYQ4"}}, "quarter"),
        ({"date_format": {"format": "YYYY"}}, "year"),
        ({"date_format": {"format": "TBD"}}, None),
        ({"date_format": 2}, "day"),
        ({}, "day"),
    ],
)
def test_get_date_precision(release, expected):
    assert igdb.get_date_precision(release) == expected


@pytest.mark.parametrize(
    ("date_string", "precision", "expected"),
    [
        ("2027-03-15", "day", "15-03-2027"),
        ("2027-03-31", "month", "Marzo 2027"),
        ("2027-03-31", "quarter", "T1 2027"),
        ("2027-12-31", "quarter", "T4 2027"),
        ("2027-12-31", "year", "2027"),
        (None, "year", "Sin fecha"),
    ],
)
def test_display_release_date_with_precision(date_string, precision, expected):
    assert igdb.display_release_date(date_string, precision) == expected


def test_display_platform_date_assumes_day_for_old_data():
    assert igdb.display_platform_date({"release_date": "2027-12-31"}) == "31-12-2027"

    year_only = {"release_date": "2027-12-31", "date_precision": "year"}

    assert igdb.display_platform_date(year_only) == "2027"


@pytest.mark.parametrize(
    ("date_string", "precision", "expected"),
    [
        ("2027-03-15", "day", ("2027-03-15", "2027-03-15")),
        ("2028-02-29", "month", ("2028-02-01", "2028-02-29")),
        ("2027-12-31", "quarter", ("2027-10-01", "2027-12-31")),
        ("2027-05-31", "quarter", ("2027-04-01", "2027-06-30")),
        ("2027-12-31", "year", ("2027-01-01", "2027-12-31")),
    ],
)
def test_release_period(date_string, precision, expected):
    start, end = igdb.release_period(date_string, precision)

    assert (start.isoformat(), end.isoformat()) == expected


def test_is_more_precise():
    assert igdb.is_more_precise("day", "year") is True
    assert igdb.is_more_precise("quarter", "month") is False
    assert igdb.is_more_precise("year", "year") is False


def test_build_platform_data_keeps_precision_when_grouping_quest():
    result = igdb.build_platform_data(
        {"id": 1, "platforms": [471, 386]},
        {386: {"date": "2027-12-31", "precision": "year"}},
    )

    assert result == [
        {
            "id": 471,
            "label": "🥽 Meta Quest",
            "release_date": "2027-12-31",
            "date_precision": "year",
        }
    ]


# ============================================================
# TIENDAS, AÑO Y PLATAFORMAS
# ============================================================


def test_get_store_links():
    # Datos reales de IGDB (The Witcher 3): orden fijo, solo tiendas
    game = {
        "websites": [
            {"type": 4, "url": "https://www.facebook.com/CDPROJEKTRED"},
            {"type": 13, "url": "https://store.steampowered.com/app/292030"},
            {"type": 23, "url": "https://store.playstation.com/en-us/concept/204794"},
            {
                "type": 22,
                "url": "https://www.xbox.com/en-us/games/store/the-witcher-3/BR765873CQJD",
            },
            {"type": 17, "url": "https://www.gog.com/game/the_witcher_3_wild_hunt"},
            # Repetida: se queda la primera
            {"type": 13, "url": "https://store.steampowered.com/app/999"},
            {"type": 16},
        ]
    }

    assert igdb.get_store_links(game) == [
        ("PlayStation", "https://store.playstation.com/es-es/concept/204794"),
        ("Xbox", "https://www.xbox.com/es-ES/games/store/the-witcher-3/BR765873CQJD"),
        ("Steam", "https://store.steampowered.com/app/292030"),
        ("GOG", "https://www.gog.com/game/the_witcher_3_wild_hunt"),
    ]


def test_get_store_links_without_websites():
    assert igdb.get_store_links({}) == []


@pytest.mark.parametrize(
    ("game", "expected"), [({"first_release_date": 1361836800}, "2013"), ({}, "TBA")]
)
def test_get_release_year(game, expected):
    assert igdb.get_release_year(game) == expected


@pytest.mark.parametrize(
    ("platform_ids", "expected"),
    [
        ([6, 167], "PS5, PC"),
        # Quest 2 y 3 son la misma plataforma
        ([471, 386], "Meta Quest"),
        ([167, 508, 6, 169, 48], "PS5, Switch 2, PC +2"),
        # PS1 no está soportada
        ([7], ""),
    ],
)
def test_get_platform_names(platform_ids, expected):
    assert igdb.get_platform_names(platform_ids) == expected
