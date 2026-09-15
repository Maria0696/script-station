from datetime import UTC, datetime

from core import igdb


def timestamp(year, month, day):
    # Crea timestamps UTC para los tests
    return int(
        datetime(
            year,
            month,
            day,
            tzinfo=UTC,
        ).timestamp()
    )


# ============================================================
# FECHAS
# ============================================================

def test_format_release_date():
    # Convierte timestamp a fecha interna
    result = igdb.format_release_date(
        timestamp(2026, 9, 15)
    )

    assert result == "2026-09-15"


def test_format_release_date_without_timestamp():
    # Devuelve None si no hay timestamp
    assert igdb.format_release_date(None) is None


def test_display_release_date():
    # Convierte la fecha al formato visible
    result = igdb.display_release_date(
        "2026-09-15"
    )

    assert result == "15-09-2026"


def test_display_release_date_without_date():
    # Muestra texto cuando no hay fecha
    assert (
        igdb.display_release_date(None)
        == "Sin fecha"
    )


# ============================================================
# PETICIONES HTTP
# ============================================================

def test_get_igdb_token(monkeypatch):
    # Comprueba la petición del token de Twitch
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
            return (
                b'{"access_token": '
                b'"test-token"}'
            )

    def fake_urlopen(req, timeout):
        captured["request"] = req
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        igdb.request,
        "urlopen",
        fake_urlopen,
    )

    result = igdb.get_igdb_token()

    assert result == "test-token"
    assert captured["timeout"] == 30

    assert (
        captured["request"].get_method()
        == "POST"
    )

    assert (
        "id.twitch.tv/oauth2/token"
        in captured["request"].full_url
    )

    assert (
        "client_id="
        in captured["request"].full_url
    )

    assert (
        "client_secret="
        in captured["request"].full_url
    )

    assert (
        "grant_type=client_credentials"
        in captured["request"].full_url
    )


def test_igdb_request(monkeypatch):
    # Comprueba una petición genérica a IGDB
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
            return (
                b'[{"id": 123, '
                b'"name": "Test Game"}]'
            )

    def fake_urlopen(req, timeout):
        captured["request"] = req
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        igdb.request,
        "urlopen",
        fake_urlopen,
    )

    result = igdb.igdb_request(
        "test-token",
        "games",
        "fields id,name;",
    )

    assert result == [
        {
            "id": 123,
            "name": "Test Game",
        }
    ]

    assert captured["timeout"] == 30

    assert (
        captured["request"].full_url
        == "https://api.igdb.com/v4/games"
    )

    assert (
        captured["request"].get_method()
        == "POST"
    )

    assert (
        captured["request"].data
        == b"fields id,name;"
    )

    headers = {
        key.lower(): value
        for key, value
        in captured[
            "request"
        ].header_items()
    }

    assert (
        headers["client-id"]
        == igdb.IGDB_CLIENT_ID
    )

    assert (
        headers["authorization"]
        == "Bearer test-token"
    )


# ============================================================
# BÚSQUEDA
# ============================================================

def test_search_igdb_games(monkeypatch):
    # Comprueba la búsqueda de juegos por nombre
    captured = {}

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    def fake_request(
        token,
        endpoint,
        query,
    ):
        captured["token"] = token
        captured["endpoint"] = endpoint
        captured["query"] = query

        return [
            {
                "id": 123,
                "name": "Test Game",
            }
        ]

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        fake_request,
    )

    result = igdb.search_igdb_games(
        'Game "Test"'
    )

    assert result == [
        {
            "id": 123,
            "name": "Test Game",
        }
    ]

    assert captured["token"] == "test-token"
    assert captured["endpoint"] == "games"

    assert (
        'search "Game \\"Test\\"";'
        in captured["query"]
    )

    assert "limit 5;" in captured["query"]


def test_search_igdb_games_escapes_backslashes(
    monkeypatch,
):
    # Escapa barras invertidas en búsquedas
    captured = {}

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    def fake_request(
        token,
        endpoint,
        query,
    ):
        captured["query"] = query

        return []

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        fake_request,
    )

    igdb.search_igdb_games(
        r"Game\Test"
    )

    assert (
        r'Game\\Test'
        in captured["query"]
    )


# ============================================================
# JUEGO INDIVIDUAL
# ============================================================

def test_get_igdb_game(monkeypatch):
    # Obtiene un juego concreto por ID
    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query: [
            {
                "id": 123,
                "name": "Test Game",
                "platforms": [167],
            }
        ],
    )

    result = igdb.get_igdb_game(
        123
    )

    assert result == {
        "id": 123,
        "name": "Test Game",
        "platforms": [167],
    }


def test_get_igdb_game_not_found(
    monkeypatch,
):
    # Devuelve None si el juego no existe
    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query: [],
    )

    assert (
        igdb.get_igdb_game(999)
        is None
    )


# ============================================================
# FECHAS POR PLATAFORMA
# ============================================================

def test_get_platform_release_dates(
    monkeypatch,
):
    # Obtiene fechas válidas por plataforma
    releases = [
        {
            "platform": 167,
            "date": timestamp(
                2026,
                9,
                15,
            ),
            "release_region": {
                "region": "europe",
            },
        },
        {
            "platform": 6,
            "date": timestamp(
                2026,
                9,
                20,
            ),
            "release_region": {
                "region": "worldwide",
            },
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {
        167: "2026-09-15",
        6: "2026-09-20",
    }


def test_get_platform_release_dates_filters_regions(
    monkeypatch,
):
    # Descarta regiones no permitidas
    releases = [
        {
            "platform": 167,
            "date": timestamp(
                2026,
                9,
                15,
            ),
            "release_region": {
                "region": "europe",
            },
        },
        {
            "platform": 6,
            "date": timestamp(
                2026,
                9,
                20,
            ),
            "release_region": {
                "region": "japan",
            },
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {
        167: "2026-09-15",
    }


def test_get_platform_release_dates_accepts_missing_region(
    monkeypatch,
):
    # Acepta lanzamientos sin región definida
    releases = [
        {
            "platform": 167,
            "date": timestamp(
                2026,
                9,
                15,
            ),
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {
        167: "2026-09-15",
    }


def test_get_platform_release_dates_ignores_unknown_platforms(
    monkeypatch,
):
    # Ignora plataformas no soportadas
    releases = [
        {
            "platform": 999999,
            "date": timestamp(
                2026,
                9,
                15,
            ),
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {}


def test_get_platform_release_dates_ignores_missing_date(
    monkeypatch,
):
    # Ignora lanzamientos sin fecha
    releases = [
        {
            "platform": 167,
            "date": None,
            "release_region": {
                "region": "europe",
            },
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {}


def test_get_platform_release_dates_keeps_first_date(
    monkeypatch,
):
    # Conserva la primera fecha encontrada
    releases = [
        {
            "platform": 167,
            "date": timestamp(
                2026,
                9,
                15,
            ),
        },
        {
            "platform": 167,
            "date": timestamp(
                2026,
                10,
                1,
            ),
        },
    ]

    monkeypatch.setattr(
        igdb,
        "get_igdb_token",
        lambda: "test-token",
    )

    monkeypatch.setattr(
        igdb,
        "igdb_request",
        lambda token, endpoint, query:
            releases,
    )

    result = (
        igdb.get_platform_release_dates(
            123
        )
    )

    assert result == {
        167: "2026-09-15",
    }


# ============================================================
# PLATAFORMAS
# ============================================================

def test_build_platform_data(
    monkeypatch,
):
    # Ordena plataformas y añade sus fechas
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            167: "2026-09-15",
            6: "2026-09-20",
        },
    )

    game = {
        "id": 123,
        "platforms": [
            6,
            167,
        ],
    }

    result = igdb.build_platform_data(
        game
    )

    assert result == [
        {
            "id": 167,
            "label": "PS5",
            "release_date":
                "2026-09-15",
        },
        {
            "id": 6,
            "label": "PC",
            "release_date":
                "2026-09-20",
        },
    ]


def test_build_platform_data_adds_platform_from_release_date(
    monkeypatch,
):
    # Añade plataformas detectadas por su fecha
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            167: "2026-09-15",
        },
    )

    game = {
        "id": 123,
        "platforms": [],
    }

    result = igdb.build_platform_data(
        game
    )

    assert result == [
        {
            "id": 167,
            "label": "PS5",
            "release_date":
                "2026-09-15",
        },
    ]


def test_build_platform_data_groups_meta_quest(
    monkeypatch,
):
    # Agrupa Quest 2 y Quest 3
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            471: "2026-10-01",
            386: "2026-10-02",
        },
    )

    game = {
        "id": 123,
        "platforms": [
            471,
            386,
        ],
    }

    result = igdb.build_platform_data(
        game
    )

    assert result == [
        {
            "id": 471,
            "label": "Meta Quest",
            "release_date":
                "2026-10-01",
        },
    ]


def test_build_platform_data_uses_second_quest_date_when_needed(
    monkeypatch,
):
    # Usa la fecha de Quest disponible
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {
            386: "2026-10-02",
        },
    )

    game = {
        "id": 123,
        "platforms": [
            471,
            386,
        ],
    }

    result = igdb.build_platform_data(
        game
    )

    assert result == [
        {
            "id": 471,
            "label": "Meta Quest",
            "release_date":
                "2026-10-02",
        },
    ]


def test_build_platform_data_without_platforms(
    monkeypatch,
):
    # Devuelve vacío si no hay plataformas
    monkeypatch.setattr(
        igdb,
        "get_platform_release_dates",
        lambda game_id: {},
    )

    game = {
        "id": 123,
    }

    result = igdb.build_platform_data(
        game
    )

    assert result == []
