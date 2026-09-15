import json
from datetime import (
    datetime,
    timezone,
)

from scripts import (
    watchlist_monitor as monitor,
)


def timestamp(
    year,
    month,
    day,
):
    # Crea timestamps UTC para los tests
    return int(
        datetime(
            year,
            month,
            day,
            tzinfo=timezone.utc,
        ).timestamp()
    )


# ============================================================
# AUTENTICACIÓN
# ============================================================

def test_get_access_token(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(
            self,
        ):
            captured[
                "raised"
            ] = True

        def json(self):
            return {
                "access_token":
                    "test-token",
            }

    def fake_post(
        url,
        params=None,
        timeout=None,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        monitor.requests,
        "post",
        fake_post,
    )

    result = (
        monitor.get_access_token()
    )

    assert (
        result
        == "test-token"
    )

    assert (
        captured["url"]
        == (
            "https://id.twitch.tv/"
            "oauth2/token"
        )
    )

    assert captured[
        "params"
    ] == {
        "client_id":
            monitor.CLIENT_ID,
        "client_secret":
            monitor.CLIENT_SECRET,
        "grant_type":
            "client_credentials",
    }

    assert (
        captured["timeout"]
        == 30
    )

    assert (
        captured["raised"]
        is True
    )


def test_get_igdb_headers():
    result = (
        monitor.get_igdb_headers(
            "test-token"
        )
    )

    assert result == {
        "Client-ID":
            monitor.CLIENT_ID,
        "Authorization":
            "Bearer test-token",
        "Accept":
            "application/json",
    }


# ============================================================
# WATCHLIST LOCAL
# ============================================================

def test_load_watchlist_missing(
    monkeypatch,
    tmp_path,
):
    path = (
        tmp_path
        / "watchlist.json"
    )

    monkeypatch.setattr(
        monitor,
        "WATCHLIST_PATH",
        path,
    )

    assert (
        monitor.load_watchlist()
        == []
    )


def test_load_watchlist(
    monkeypatch,
    tmp_path,
):
    path = (
        tmp_path
        / "watchlist.json"
    )

    data = [
        {
            "id": 123,
            "name":
                "Test Game",
        }
    ]

    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        monitor,
        "WATCHLIST_PATH",
        path,
    )

    assert (
        monitor.load_watchlist()
        == data
    )


def test_save_watchlist(
    monkeypatch,
    tmp_path,
):
    path = (
        tmp_path
        / "watchlist.json"
    )

    monkeypatch.setattr(
        monitor,
        "WATCHLIST_PATH",
        path,
    )

    data = [
        {
            "id": 123,
            "name":
                "Pokémon Test",
        }
    ]

    monitor.save_watchlist(
        data
    )

    content = (
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        json.loads(content)
        == data
    )

    assert (
        content.endswith("\n")
    )

    assert (
        "Pokémon Test"
        in content
    )


# ============================================================
# JUEGOS DE IGDB
# ============================================================

def test_get_games_from_igdb_empty():
    assert (
        monitor
        .get_games_from_igdb(
            "token",
            [],
        )
        == {}
    )


def test_get_games_from_igdb(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return [
                {
                    "id": 123,
                    "name":
                        "Game One",
                },
                {
                    "id": 456,
                    "name":
                        "Game Two",
                },
            ]

    def fake_post(
        url,
        headers=None,
        data=None,
        timeout=None,
    ):
        captured["url"] = url
        captured["headers"] = headers
        captured["query"] = data
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        monitor.requests,
        "post",
        fake_post,
    )

    result = (
        monitor
        .get_games_from_igdb(
            "test-token",
            [
                123,
                456,
            ],
        )
    )

    assert result == {
        123: {
            "id": 123,
            "name":
                "Game One",
        },
        456: {
            "id": 456,
            "name":
                "Game Two",
        },
    }

    assert (
        captured["url"]
        == (
            "https://api.igdb.com/"
            "v4/games"
        )
    )

    assert (
        "where id = (123,456);"
        in captured["query"]
    )

    assert (
        captured["timeout"]
        == 30
    )


# ============================================================
# FECHAS DE LANZAMIENTO
# ============================================================

def test_get_release_dates_from_igdb_empty():
    assert (
        monitor
        .get_release_dates_from_igdb(
            "token",
            [],
        )
        == {}
    )


def test_get_release_dates_from_igdb(
    monkeypatch,
):
    releases = [
        {
            "game": 123,
            "platform": 167,
            "date": timestamp(
                2026,
                9,
                20,
            ),
            "release_region": {
                "region":
                    "europe",
            },
        },
        {
            "game": {
                "id": 123,
            },
            "platform": 6,
            "date": timestamp(
                2026,
                9,
                25,
            ),
            "release_region": {
                "region":
                    "worldwide",
            },
        },
        {
            "game": 123,
            "platform": 167,
            "date": timestamp(
                2026,
                10,
                1,
            ),
        },
        {
            "game": 123,
            "platform": 130,
            "date": timestamp(
                2026,
                9,
                22,
            ),
            "release_region": {
                "region":
                    "japan",
            },
        },
        {
            "game": 123,
            "platform": 999999,
            "date": timestamp(
                2026,
                9,
                22,
            ),
        },
        {
            "game": 123,
            "platform": 508,
            "date": None,
        },
    ]

    class FakeResponse:
        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return releases

    monkeypatch.setattr(
        monitor.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(),
    )

    result = (
        monitor
        .get_release_dates_from_igdb(
            "test-token",
            [123],
        )
    )

    assert result == {
        123: {
            167:
                "2026-09-20",
            6:
                "2026-09-25",
        }
    }


# ============================================================
# FECHAS
# ============================================================

def test_timestamp_to_date():
    result = (
        monitor.timestamp_to_date(
            timestamp(
                2026,
                9,
                20,
            )
        )
    )

    assert (
        result
        == "2026-09-20"
    )


def test_timestamp_to_date_empty():
    assert (
        monitor
        .timestamp_to_date(
            None
        )
        is None
    )


def test_display_date():
    assert (
        monitor.display_date(
            "2026-09-20"
        )
        == "20-09-2026"
    )


def test_display_date_empty():
    assert (
        monitor.display_date(
            None
        )
        == "Sin fecha"
    )


# ============================================================
# NOTIFICACIONES
# ============================================================

def test_send_notification(
    monkeypatch,
):
    captured = {}

    def fake_huginn(
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        captured[
            "text"
        ] = text

        captured[
            "reply_markup"
        ] = reply_markup

        captured[
            "parse_mode"
        ] = parse_mode

        captured[
            "chat_id"
        ] = chat_id

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        monitor.notifications,
        "huginn",
        fake_huginn,
    )

    result = (
        monitor.send_notification(
            "Test message"
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured["text"]
        == "Test message"
    )

    assert (
        captured["reply_markup"]
        is None
    )

    assert (
        captured["parse_mode"]
        is None
    )

    assert (
        captured["chat_id"]
        is None
    )


# ============================================================
# PLATAFORMAS
# ============================================================

def test_build_platforms():
    game = {
        "platforms": [
            6,
            167,
        ],
    }

    release_dates = {
        167:
            "2026-09-20",
        6:
            "2026-09-25",
    }

    result = (
        monitor.build_platforms(
            game,
            release_dates,
        )
    )

    assert result == [
        {
            "id": 167,
            "label":
                "🔵 PS5",
            "release_date":
                "2026-09-20",
        },
        {
            "id": 6,
            "label":
                "💻 PC",
            "release_date":
                "2026-09-25",
        },
    ]


def test_build_platforms_adds_release_platform():
    game = {
        "platforms": [],
    }

    result = (
        monitor.build_platforms(
            game,
            {
                167:
                    "2026-09-20",
            },
        )
    )

    assert result == [
        {
            "id": 167,
            "label":
                "🔵 PS5",
            "release_date":
                "2026-09-20",
        }
    ]


def test_build_platforms_groups_meta_quest():
    game = {
        "platforms": [
            471,
            386,
        ],
    }

    result = (
        monitor.build_platforms(
            game,
            {},
        )
    )

    assert result == [
        {
            "id": 471,
            "label":
                "🥽 Meta Quest",
            "release_date":
                None,
        }
    ]


# ============================================================
# MENSAJES DE CAMBIO
# ============================================================

def test_build_change_message_new_date():
    result = (
        monitor
        .build_change_message(
            "Test Game",
            "🔵 PS5",
            None,
            "2026-09-20",
        )
    )

    assert result == (
        "📅 NUEVA FECHA DE LANZAMIENTO\n\n"
        "🎮 Test Game\n"
        "🔵 PS5\n"
        "📅 20-09-2026"
    )


def test_build_change_message_removed_date():
    result = (
        monitor
        .build_change_message(
            "Test Game",
            "🔵 PS5",
            "2026-09-20",
            None,
        )
    )

    assert (
        "⚠️ FECHA DE LANZAMIENTO RETIRADA"
        in result
    )

    assert (
        "Antes: 20-09-2026"
        in result
    )

    assert (
        "Ahora: Por confirmar"
        in result
    )


def test_build_change_message_delay():
    result = (
        monitor
        .build_change_message(
            "Test Game",
            "🔵 PS5",
            "2026-09-20",
            "2026-10-01",
        )
    )

    assert (
        "⏳ RETRASO DE LANZAMIENTO"
        in result
    )

    assert (
        "Antes: 20-09-2026"
        in result
    )

    assert (
        "Ahora: 01-10-2026"
        in result
    )


def test_build_change_message_advance():
    result = (
        monitor
        .build_change_message(
            "Test Game",
            "🔵 PS5",
            "2026-10-01",
            "2026-09-20",
        )
    )

    assert (
        "⏩ ADELANTO DE LANZAMIENTO"
        in result
    )


def test_build_change_message_same_date():
    result = (
        monitor
        .build_change_message(
            "Test Game",
            "🔵 PS5",
            "2026-09-20",
            "2026-09-20",
        )
    )

    assert (
        result is None
    )


# ============================================================
# MONITOR
# ============================================================

def test_monitor_watchlist_empty(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        list,
    )

    result = (
        monitor.monitor_watchlist()
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        result is False
    )

    assert (
        "Watchlist is empty."
        in output
    )


def test_monitor_watchlist_game_not_found(
    monkeypatch,
    capsys,
):
    watchlist = [
        {
            "id": 123,
            "name":
                "Missing Game",
        }
    ]

    saved = []

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            watchlist,
    )

    monkeypatch.setattr(
        monitor,
        "get_access_token",
        lambda:
            "token",
    )

    monkeypatch.setattr(
        monitor,
        "get_games_from_igdb",
        lambda token, ids:
            {},
    )

    monkeypatch.setattr(
        monitor,
        "get_release_dates_from_igdb",
        lambda token, ids:
            {},
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data:
            saved.append(
                data
            ),
    )

    result = (
        monitor.monitor_watchlist()
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        result is False
    )

    assert (
        saved == []
    )

    assert (
        "Game not found: "
        "Missing Game (123)"
        in output
    )


def test_monitor_watchlist_migrates_old_format(
    monkeypatch,
    capsys,
):
    watchlist = [
        {
            "id": 123,
            "name":
                "Old Game",
            "platforms": [
                "PS5",
                "PC",
            ],
        }
    ]

    saved = []

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            watchlist,
    )

    monkeypatch.setattr(
        monitor,
        "get_access_token",
        lambda:
            "token",
    )

    monkeypatch.setattr(
        monitor,
        "get_games_from_igdb",
        lambda token, ids: {
            123: {
                "id": 123,
                "name":
                    "New Name",
                "first_release_date":
                    timestamp(
                        2026,
                        9,
                        20,
                    ),
                "platforms": [
                    167,
                ],
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "get_release_dates_from_igdb",
        lambda token, ids: {
            123: {
                167:
                    "2026-09-20",
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data:
            saved.append(
                data.copy()
            ),
    )

    result = (
        monitor.monitor_watchlist()
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        result is True
    )

    assert (
        "Migrated platforms: New Name"
        in output
    )

    assert (
        len(saved)
        == 1
    )

    assert (
        watchlist[0]["name"]
        == "New Name"
    )

    assert (
        watchlist[0][
            "release_date"
        ]
        == "2026-09-20"
    )

    assert (
        watchlist[0][
            "platforms"
        ]
        == [
            {
                "id": 167,
                "label":
                    "🔵 PS5",
                "release_date":
                    "2026-09-20",
            }
        ]
    )


def test_monitor_watchlist_date_changed(
    monkeypatch,
):
    watchlist = [
        {
            "id": 123,
            "name":
                "Test Game",
            "release_date":
                "2026-09-20",
            "platforms": [
                {
                    "id":
                        167,
                    "label":
                        "🔵 PS5",
                    "release_date":
                        "2026-09-20",
                }
            ],
        }
    ]

    messages = []
    saved = []

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            watchlist,
    )

    monkeypatch.setattr(
        monitor,
        "get_access_token",
        lambda:
            "token",
    )

    monkeypatch.setattr(
        monitor,
        "get_games_from_igdb",
        lambda token, ids: {
            123: {
                "id": 123,
                "name":
                    "Test Game",
                "first_release_date":
                    timestamp(
                        2026,
                        10,
                        1,
                    ),
                "platforms": [
                    167,
                ],
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "get_release_dates_from_igdb",
        lambda token, ids: {
            123: {
                167:
                    "2026-10-01",
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message:
            messages.append(
                message
            ),
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data:
            saved.append(
                data.copy()
            ),
    )

    result = (
        monitor.monitor_watchlist()
    )

    assert (
        result is True
    )

    assert (
        len(messages)
        == 1
    )

    assert (
        len(saved)
        == 1
    )

    assert (
        "⏳ RETRASO DE LANZAMIENTO"
        in messages[0]
    )

    assert (
        watchlist[0][
            "platforms"
        ][0][
            "release_date"
        ]
        == "2026-10-01"
    )


def test_monitor_watchlist_without_changes(
    monkeypatch,
):
    watchlist = [
        {
            "id": 123,
            "name":
                "Test Game",
            "release_date":
                "2026-09-20",
            "platforms": [
                {
                    "id":
                        167,
                    "label":
                        "🔵 PS5",
                    "release_date":
                        "2026-09-20",
                }
            ],
        }
    ]

    saved = []
    sent = []

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            watchlist,
    )

    monkeypatch.setattr(
        monitor,
        "get_access_token",
        lambda:
            "token",
    )

    monkeypatch.setattr(
        monitor,
        "get_games_from_igdb",
        lambda token, ids: {
            123: {
                "id": 123,
                "name":
                    "Test Game",
                "first_release_date":
                    timestamp(
                        2026,
                        9,
                        20,
                    ),
                "platforms": [
                    167,
                ],
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "get_release_dates_from_igdb",
        lambda token, ids: {
            123: {
                167:
                    "2026-09-20",
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data:
            saved.append(
                data
            ),
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message:
            sent.append(
                message
            ),
    )

    result = (
        monitor.monitor_watchlist()
    )

    assert (
        result is False
    )

    assert (
        saved == []
    )

    assert (
        sent == []
    )


def test_monitor_watchlist_platform_change(
    monkeypatch,
):
    watchlist = [
        {
            "id": 123,
            "name":
                "Test Game",
            "platforms": [
                {
                    "id":
                        167,
                    "label":
                        "🔵 PS5",
                    "release_date":
                        None,
                }
            ],
        }
    ]

    saved = []

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            watchlist,
    )

    monkeypatch.setattr(
        monitor,
        "get_access_token",
        lambda:
            "token",
    )

    monkeypatch.setattr(
        monitor,
        "get_games_from_igdb",
        lambda token, ids: {
            123: {
                "id": 123,
                "name":
                    "Test Game",
                "platforms": [
                    167,
                    6,
                ],
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "get_release_dates_from_igdb",
        lambda token, ids:
            {},
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data:
            saved.append(
                data.copy()
            ),
    )

    result = (
        monitor.monitor_watchlist()
    )

    assert (
        result is True
    )

    assert (
        len(saved)
        == 1
    )

    assert (
        len(
            watchlist[0][
                "platforms"
            ]
        )
        == 2
    )


# ============================================================
# MAIN
# ============================================================

def test_main(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        monitor,
        "monitor_watchlist",
        lambda:
            called.append(
                True
            ),
    )

    monitor.main()

    assert called == [
        True,
    ]
