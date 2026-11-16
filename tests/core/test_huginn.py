from datetime import datetime

from core import huginn


def test_build_title_with_icon():
    result = huginn.build_title("TEST", icon="🤖", indent=2)

    assert result == ("━━━━━━━━━━━━━━━━━━━\n  🤖 TEST\n━━━━━━━━━━━━━━━━━━━\n\n")


def test_build_title_without_icon():
    result = huginn.build_title("TEST")

    assert result == ("━━━━━━━━━━━━━━━━━━━\nTEST\n━━━━━━━━━━━━━━━━━━━\n\n")


def test_build_help_message():
    result = huginn.build_help_message()

    assert "🤖 COMANDOS" in result
    assert "/watch nombre" in result
    assert "/watchlist" in result
    assert "/next" in result
    assert "/unwatch" in result
    assert "/help" in result


def test_build_watch_search_message():
    message = huginn.build_watch_search_message()

    assert message.startswith("¿Qué juego quieres añadir?")
    assert "nombre completo" in message


def test_build_watch_added_message():
    assert (
        huginn.build_watch_added_message({"name": "Test Game"})
        == "✅ Añadido: Test Game"
    )


def test_build_already_added_message():
    assert huginn.build_already_added_message({"name": "Test Game"}) == (
        "ℹ️ Ese juego ya estaba en tu lista: Test Game"
    )


def test_build_unwatch_message():
    assert huginn.build_unwatch_message() == "¿Qué juego quieres eliminar?"


def test_build_removed_message():
    assert (
        huginn.build_removed_message({"name": "Test Game"}) == "🗑️ Eliminado: Test Game"
    )


def test_build_watchlist_message_empty(monkeypatch):
    monkeypatch.setattr(huginn, "get_watchlist", lambda: ([], "sha"))

    assert huginn.build_watchlist_message() == "👀 Tu lista está vacía."


def test_build_watchlist_message_current_format(monkeypatch):
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [
                {
                    "id": 1,
                    "name": "Test Game",
                    "platforms": [
                        {"label": "PS5", "release_date": "2026-09-20"},
                        {"label": "PC", "release_date": None},
                    ],
                }
            ],
            "sha",
        ),
    )

    result = huginn.build_watchlist_message()

    assert "👀 MI LISTADO DE JUEGOS" in result
    assert "🎮 Test Game" in result
    assert "PS5 — 20-09-2026" in result
    assert "PC — Sin fecha" in result


def test_build_watchlist_message_legacy_format(monkeypatch):
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [
                {
                    "id": 1,
                    "name": "Old Game",
                    "platforms": ["PS5", "PC"],
                    "release_date": "2026-10-01",
                }
            ],
            "sha",
        ),
    )

    result = huginn.build_watchlist_message()

    assert "🎮 Old Game" in result

    assert "PS5 | PC — 01-10-2026" in result


def test_build_watchlist_message_without_platforms(monkeypatch):
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [{"id": 1, "name": "Unknown Game", "release_date": "2026-11-01"}],
            "sha",
        ),
    )

    result = huginn.build_watchlist_message()

    assert "Plataformas por confirmar — 01-11-2026" in result


def test_parse_release_date():
    result = huginn.parse_release_date("2026-09-20")

    assert result.isoformat() == "2026-09-20"


def test_parse_release_date_without_date():
    assert huginn.parse_release_date(None) is None


def test_parse_release_date_invalid():
    assert huginn.parse_release_date("invalid-date") is None


def test_get_upcoming_games(monkeypatch):
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 14, 12, 0, tzinfo=tz)

    watchlist = [
        {
            "name": "Game B",
            "platforms": [
                {"label": "PC", "release_date": "2026-09-20"},
                {"label": "PS5", "release_date": "2026-09-18"},
                {"label": "PS4", "release_date": "2026-09-01"},
                {"label": "Xbox", "release_date": "invalid"},
            ],
        },
        {"name": "Game A", "platforms": ["PS5", "PC"], "release_date": "2026-09-16"},
        {"name": "Game C", "release_date": "2026-09-17"},
        {"name": "Past Game", "release_date": "2026-09-01"},
    ]

    monkeypatch.setattr(huginn, "datetime", FakeDatetime)

    monkeypatch.setattr(huginn, "get_watchlist", lambda: (watchlist, "sha"))

    result = huginn.get_upcoming_games()

    assert [game["name"] for game in result] == ["Game A", "Game C", "Game B"]

    assert result[0]["releases"][0]["label"] == "PS5 | PC"

    assert result[1]["releases"][0]["label"] == "Plataformas por confirmar"

    assert [release["label"] for release in result[2]["releases"]] == ["PS5", "PC"]


def test_get_upcoming_games_limits_results(monkeypatch):
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 14, tzinfo=tz)

    watchlist = [
        {"name": f"Game {index}", "release_date": f"2026-09-{15 + index:02d}"}
        for index in range(6)
    ]

    monkeypatch.setattr(huginn, "datetime", FakeDatetime)

    monkeypatch.setattr(huginn, "get_watchlist", lambda: (watchlist, "sha"))

    result = huginn.get_upcoming_games()

    assert len(result) == 5

    assert [game["name"] for game in result] == [
        "Game 0",
        "Game 1",
        "Game 2",
        "Game 3",
        "Game 4",
    ]


def test_build_next_message_empty(monkeypatch):
    monkeypatch.setattr(huginn, "get_upcoming_games", list)

    assert huginn.build_next_message() == (
        "⏭️ No tienes próximos lanzamientos con fecha."
    )


def test_build_next_message(monkeypatch):
    monkeypatch.setattr(
        huginn,
        "get_upcoming_games",
        lambda: [
            {
                "name": "Test Game",
                "releases": [
                    {"label": "PS5", "date": "2026-09-20", "display": "20-09-2026"},
                    {"label": "PC", "date": "2027-12-31", "display": "2027"},
                ],
            }
        ],
    )

    result = huginn.build_next_message()

    assert "⏭️ PRÓXIMOS LANZAMIENTOS" in result

    assert "🎮 Test Game" in result
    assert "PS5 — 20-09-2026" in result
    assert "PC — 2027" in result


def test_build_search_keyboard():
    # Año y plataformas distinguen juegos con el mismo nombre
    games = [
        {
            "id": 123,
            "name": "Tomb Raider",
            "first_release_date": 1361836800,
            "platforms": [6, 48, 49],
        },
        # Sin fecha y en plataformas no soportadas (PS1)
        {"id": 456, "name": "Tomb Raider", "platforms": [7]},
    ]

    result = huginn.build_search_keyboard(games)

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text": "Tomb Raider (2013) · PC, PS4, Xbox One",
                    "callback_data": "watch:123",
                }
            ],
            [{"text": "Tomb Raider (TBA)", "callback_data": "watch:456"}],
        ]
    }


def test_build_unwatch_keyboard():
    watchlist = [{"id": 123, "name": "Game One"}]

    result = huginn.build_unwatch_keyboard(watchlist)

    assert result == {
        "inline_keyboard": [[{"text": "❌ Game One", "callback_data": "unwatch:123"}]]
    }


def test_add_game_to_watchlist_not_found(monkeypatch):
    monkeypatch.setattr(huginn, "get_igdb_game", lambda game_id: None)

    result = huginn.add_game_to_watchlist(999)

    assert result == (None, False)


def fake_update_watchlist(monkeypatch, watchlist):
    saved = []

    def update(change, message=None):
        result, changed = change(watchlist)

        if changed:
            saved.append([dict(item) for item in watchlist])

        return result

    monkeypatch.setattr(huginn, "update_watchlist", update)

    return saved


def test_add_game_to_watchlist_existing(monkeypatch):
    game = {"id": 123, "name": "Test Game"}

    existing = {"id": 123, "name": "Test Game"}

    monkeypatch.setattr(huginn, "get_igdb_game", lambda game_id: game)

    saved = fake_update_watchlist(monkeypatch, [existing])

    result = huginn.add_game_to_watchlist(123)

    assert result == (existing, False)
    assert saved == []


def test_add_game_to_watchlist(monkeypatch):
    game = {"id": 123, "name": "Test Game", "first_release_date": 123456789}

    monkeypatch.setattr(huginn, "get_igdb_game", lambda game_id: game)

    monkeypatch.setattr(huginn, "format_release_date", lambda timestamp: "2026-09-20")

    monkeypatch.setattr(
        huginn,
        "build_platform_data",
        lambda game: [{"label": "PS5", "release_date": "2026-09-20"}],
    )

    saved = fake_update_watchlist(monkeypatch, [])

    result, added = huginn.add_game_to_watchlist(123)

    assert added is True

    assert saved == [
        [
            {
                "id": 123,
                "name": "Test Game",
                "release_date": "2026-09-20",
                "platforms": [{"label": "PS5", "release_date": "2026-09-20"}],
            }
        ]
    ]

    assert result["release_date"] == "2026-09-20"

    assert result["platform_data"] == [{"label": "PS5", "release_date": "2026-09-20"}]


def test_remove_game_from_watchlist_not_found(monkeypatch):
    saved = fake_update_watchlist(monkeypatch, [])

    result = huginn.remove_game_from_watchlist(123)

    assert result == (None, False)
    assert saved == []


def test_remove_game_from_watchlist(monkeypatch):
    watchlist = [{"id": 123, "name": "Game One"}, {"id": 456, "name": "Game Two"}]

    saved = fake_update_watchlist(monkeypatch, watchlist)

    game, removed = huginn.remove_game_from_watchlist(123)

    assert removed is True

    assert game == {"id": 123, "name": "Game One"}

    assert saved == [[{"id": 456, "name": "Game Two"}]]


def test_handle_watch_callback_not_found(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "add_game_to_watchlist", lambda game_id: (None, False))

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_watch_callback("123", 999)

    assert sent == [("123", ("❌ No he podido encontrar el juego."))]


def test_handle_watch_callback_existing(monkeypatch):
    sent = []

    game = {"id": 123, "name": "Test Game"}

    monkeypatch.setattr(huginn, "add_game_to_watchlist", lambda game_id: (game, False))

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_watch_callback("123", 123)

    assert sent == [("123", ("ℹ️ Ese juego ya estaba en tu lista: Test Game"))]


def test_handle_watch_callback_added(monkeypatch):
    sent = []

    game = {"id": 123, "name": "Test Game"}

    monkeypatch.setattr(huginn, "add_game_to_watchlist", lambda game_id: (game, True))

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_watch_callback("123", 123)

    assert sent == [("123", "✅ Añadido: Test Game")]


def test_handle_unwatch_callback_missing(monkeypatch):
    sent = []

    monkeypatch.setattr(
        huginn, "remove_game_from_watchlist", lambda game_id: (None, False)
    )

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_unwatch_callback("123", 123)

    assert sent == [("123", ("ℹ️ Ese juego ya no está en tu lista."))]


def test_handle_unwatch_callback_removed(monkeypatch):
    sent = []

    game = {"id": 123, "name": "Test Game"}

    monkeypatch.setattr(
        huginn, "remove_game_from_watchlist", lambda game_id: (game, True)
    )

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_unwatch_callback("123", 123)

    assert sent == [("123", "🗑️ Eliminado: Test Game")]


def test_handle_huginn_callback_unauthorized(monkeypatch):
    answered = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id: answered.append(callback_id),
    )

    result = huginn.handle_huginn_callback(
        {"id": "callback-1", "data": "watch:123", "message": {"chat": {"id": "999999"}}}
    )

    assert result == {"ok": True}

    assert answered == []


def test_handle_huginn_callback_watch(monkeypatch):
    answered = []
    handled = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id: answered.append(callback_id),
    )

    monkeypatch.setattr(
        huginn,
        "handle_watch_callback",
        lambda chat_id, game_id: handled.append((chat_id, game_id)),
    )

    result = huginn.handle_huginn_callback(
        {
            "id": "callback-1",
            "data": "watch:123",
            "message": {"chat": {"id": huginn.HUGINN_CHAT_ID}},
        }
    )

    assert result == {"ok": True}

    assert answered == ["callback-1"]

    assert handled == [(huginn.HUGINN_CHAT_ID, 123)]


def test_handle_huginn_callback_unwatch(monkeypatch):
    handled = []

    monkeypatch.setattr(huginn, "answer_huginn_callback", lambda callback_id: None)

    monkeypatch.setattr(
        huginn,
        "handle_unwatch_callback",
        lambda chat_id, game_id: handled.append((chat_id, game_id)),
    )

    result = huginn.handle_huginn_callback(
        {
            "id": "callback-1",
            "data": "unwatch:456",
            "message": {"chat": {"id": huginn.HUGINN_CHAT_ID}},
        }
    )

    assert result == {"ok": True}

    assert handled == [(huginn.HUGINN_CHAT_ID, 456)]


def test_handle_huginn_callback_without_id(monkeypatch):
    answered = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id: answered.append(callback_id),
    )

    result = huginn.handle_huginn_callback(
        {"data": "unknown", "message": {"chat": {"id": huginn.HUGINN_CHAT_ID}}}
    )

    assert result == {"ok": True}

    assert answered == []


def test_handle_huginn_message_unauthorized(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    result = huginn.handle_huginn_message({"chat": {"id": "999999"}, "text": "/help"})

    assert result == {"ok": True}

    assert sent == []


def test_handle_huginn_help(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "build_help_message", lambda: "HELP")

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    result = huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "  /help  "}
    )

    assert result == {"ok": True}

    assert sent == [(huginn.HUGINN_CHAT_ID, "HELP")]


def test_handle_huginn_next(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "build_next_message", lambda: "NEXT")

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/next"}
    )

    assert sent == [(huginn.HUGINN_CHAT_ID, "NEXT")]


def test_handle_huginn_watchlist(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "build_watchlist_message", lambda: "WATCHLIST")

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/watchlist"}
    )

    assert sent == [(huginn.HUGINN_CHAT_ID, "WATCHLIST")]


def test_handle_huginn_unwatch_empty(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "get_watchlist", lambda: ([], "sha"))

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/unwatch"}
    )

    assert sent == [(huginn.HUGINN_CHAT_ID, "👀 Tu lista está vacía.")]


def test_handle_huginn_unwatch_with_games(monkeypatch):
    sent = []

    watchlist = [{"id": 123, "name": "Test Game"}]

    monkeypatch.setattr(huginn, "get_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/unwatch"}
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "¿Qué juego quieres eliminar?",
            {
                "inline_keyboard": [
                    [{"text": "❌ Test Game", "callback_data": "unwatch:123"}]
                ]
            },
        )
    ]


def test_handle_huginn_watch_without_name(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/watch"}
    )

    assert sent == [(huginn.HUGINN_CHAT_ID, ("Uso: /watch nombre del juego"))]


def test_handle_huginn_watch_empty_search(monkeypatch):
    sent = []

    class FakeText:
        def strip(self):
            return "/watch "

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    result = huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": FakeText()}
    )

    assert result == {"ok": True}

    assert sent == [(huginn.HUGINN_CHAT_ID, ("Uso: /watch nombre del juego"))]


def test_handle_huginn_watch_not_found(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "search_igdb_games", lambda search_term: [])

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/watch Unknown Game"}
    )

    assert sent == [(huginn.HUGINN_CHAT_ID, ("❌ No he encontrado ningún juego."))]


def test_handle_huginn_watch_results(monkeypatch):
    sent = []

    games = [{"id": 123, "name": "Test Game"}]

    captured = {}

    def fake_search(search_term):
        captured["term"] = search_term

        return games

    monkeypatch.setattr(huginn, "search_igdb_games", fake_search)

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/watch   Test Game  "}
    )

    assert captured["term"] == "Test Game"

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            huginn.build_watch_search_message(),
            {
                "inline_keyboard": [
                    [{"text": "Test Game (TBA)", "callback_data": "watch:123"}]
                ]
            },
        )
    ]


def test_handle_huginn_unknown_command(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "send_huginn_message", lambda *args: sent.append(args))

    result = huginn.handle_huginn_message(
        {"chat": {"id": huginn.HUGINN_CHAT_ID}, "text": "/unknown"}
    )

    assert result == {"ok": True}

    assert sent == []


def test_handle_huginn_update_callback(monkeypatch):
    callback = {"id": "callback-1"}

    monkeypatch.setattr(
        huginn,
        "handle_huginn_callback",
        lambda received: {"type": "callback", "data": received},
    )

    result = huginn.handle_huginn_update({"callback_query": callback})

    assert result == {"type": "callback", "data": callback}


def test_handle_huginn_update_message(monkeypatch):
    message = {"text": "/help"}

    monkeypatch.setattr(
        huginn,
        "handle_huginn_message",
        lambda received: {"type": "message", "data": received},
    )

    result = huginn.handle_huginn_update({"message": message})

    assert result == {"type": "message", "data": message}


def test_handle_huginn_update_empty():
    result = huginn.handle_huginn_update({})

    assert result == {"ok": True}


def test_build_watchlist_message_shows_precision(monkeypatch):
    platform = {
        "id": 167,
        "label": "🔵 PS5",
        "release_date": "2027-12-31",
        "date_precision": "year",
    }

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: ([{"id": 1, "name": "Ill", "platforms": [platform]}], "sha"),
    )

    assert "🔵 PS5 — 2027" in huginn.build_watchlist_message()


ACTIVE_GAME = {
    "id": 1,
    "name": "Ill",
    "platforms": [
        {
            "id": 167,
            "label": "🔵 PS5",
            "release_date": "2099-12-31",
            "date_precision": "year",
        }
    ],
}

RELEASED_GAMES = [
    {
        "id": 2,
        "name": "Marvel's Wolverine",
        "status": "released",
        "released_on": "2026-09-15",
        "platforms": [],
    },
    {
        "id": 3,
        "name": "Newer Game",
        "status": "released",
        "released_on": "2026-10-20",
        "platforms": [],
    },
]


def mock_watchlist(monkeypatch, games):
    monkeypatch.setattr(huginn, "get_watchlist", lambda: (games, "sha"))


def test_build_watchlist_message_hides_released_games(monkeypatch):
    mock_watchlist(monkeypatch, [ACTIVE_GAME, *RELEASED_GAMES])

    result = huginn.build_watchlist_message()

    assert "🎮 Ill" in result
    assert "Wolverine" not in result
    assert result.endswith("📦 Ya lanzados: 2 (/released)")


def test_build_watchlist_message_only_released_games(monkeypatch):
    mock_watchlist(monkeypatch, RELEASED_GAMES)

    assert huginn.build_watchlist_message() == (
        "👀 No tienes juegos pendientes de salir.\n\n📦 Ya lanzados: 2 (/released)"
    )


def test_build_released_message(monkeypatch):
    mock_watchlist(monkeypatch, [ACTIVE_GAME, *RELEASED_GAMES])

    result = huginn.build_released_message()

    assert "📦 YA LANZADOS" in result
    assert "Ill" not in result
    assert result.index("Newer Game") < result.index("Marvel's Wolverine")
    assert "      15-09-2026" in result


def test_build_released_message_empty(monkeypatch):
    mock_watchlist(monkeypatch, [ACTIVE_GAME])

    assert huginn.build_released_message() == (
        "📦 Todavía no ha salido ningún juego de tu lista."
    )


def test_get_upcoming_games_skips_released_games(monkeypatch):
    mock_watchlist(monkeypatch, [ACTIVE_GAME, *RELEASED_GAMES])

    names = [game["name"] for game in huginn.get_upcoming_games()]

    assert names == ["Ill"]


def test_handle_released_command(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "build_released_message", lambda: "released list")
    monkeypatch.setattr(
        huginn, "send_huginn_message", lambda chat_id, text: sent.append(text)
    )

    huginn.handle_huginn_message(
        {"chat": {"id": int(huginn.HUGINN_CHAT_ID)}, "text": "/released"}
    )

    assert sent == ["released list"]


def test_help_lists_released_command():
    assert "/released" in huginn.build_help_message()


def failing_dispatch(update):
    raise OSError("IGDB unavailable")


def test_update_error_is_reported_in_chat(monkeypatch, caplog):
    sent = []

    monkeypatch.setattr(huginn, "dispatch_huginn_update", failing_dispatch)
    monkeypatch.setattr(
        huginn, "send_huginn_message", lambda chat_id, text: sent.append(text)
    )

    result = huginn.handle_huginn_update(
        {"message": {"chat": {"id": int(huginn.HUGINN_CHAT_ID)}, "text": "/next"}}
    )

    assert result == {"ok": True}
    assert sent == [huginn.ERROR_MESSAGE]
    assert "Huginn could not process an update" in caplog.text


def test_update_error_is_not_reported_to_other_chats(monkeypatch):
    sent = []

    monkeypatch.setattr(huginn, "dispatch_huginn_update", failing_dispatch)
    monkeypatch.setattr(
        huginn, "send_huginn_message", lambda chat_id, text: sent.append(text)
    )

    huginn.handle_huginn_update({"message": {"chat": {"id": 999}, "text": "/next"}})

    assert sent == []


def test_update_error_survives_failed_error_message(monkeypatch, caplog):
    def failing_send(chat_id, text):
        raise OSError("Telegram unavailable")

    monkeypatch.setattr(huginn, "dispatch_huginn_update", failing_dispatch)
    monkeypatch.setattr(huginn, "send_huginn_message", failing_send)

    result = huginn.handle_huginn_update(
        {"callback_query": {"message": {"chat": {"id": int(huginn.HUGINN_CHAT_ID)}}}}
    )

    assert result == {"ok": True}
    assert "Could not send the Huginn error message" in caplog.text
