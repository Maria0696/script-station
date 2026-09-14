from datetime import datetime

from core import huginn


# ============================================================
# ESTILO
# ============================================================

def test_build_title_with_icon():
    # Construye título con icono e indentación
    result = huginn.build_title(
        "TEST",
        icon="🤖",
        indent=2,
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        "  🤖 TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


def test_build_title_without_icon():
    # Construye título sin icono
    result = huginn.build_title(
        "TEST"
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        "TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ============================================================
# MENSAJES
# ============================================================

def test_build_help_message():
    # Construye la ayuda de Huginn
    result = huginn.build_help_message()

    assert "🤖 COMANDOS" in result
    assert "/watch nombre" in result
    assert "/watchlist" in result
    assert "/next" in result
    assert "/unwatch" in result
    assert "/help" in result


def test_build_watch_search_message():
    # Construye el mensaje de selección
    assert (
        huginn.build_watch_search_message()
        == "¿Qué juego quieres añadir?"
    )


def test_build_watch_added_message():
    # Confirma un juego añadido
    assert (
        huginn.build_watch_added_message(
            {"name": "Test Game"}
        )
        == "✅ Añadido: Test Game"
    )


def test_build_already_added_message():
    # Informa de un juego ya guardado
    assert (
        huginn.build_already_added_message(
            {"name": "Test Game"}
        )
        == (
            "ℹ️ Ese juego ya estaba "
            "en tu lista: Test Game"
        )
    )


def test_build_unwatch_message():
    # Construye el mensaje para eliminar
    assert (
        huginn.build_unwatch_message()
        == "¿Qué juego quieres eliminar?"
    )


def test_build_removed_message():
    # Confirma un juego eliminado
    assert (
        huginn.build_removed_message(
            {"name": "Test Game"}
        )
        == "🗑️ Eliminado: Test Game"
    )


def test_build_watchlist_message_empty(
    monkeypatch,
):
    # Muestra mensaje si la lista está vacía
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: ([], "sha"),
    )

    assert (
        huginn.build_watchlist_message()
        == "👀 Tu lista está vacía."
    )


def test_build_watchlist_message_current_format(
    monkeypatch,
):
    # Muestra plataformas con formato actual
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [
                {
                    "id": 1,
                    "name": "Test Game",
                    "platforms": [
                        {
                            "label": "PS5",
                            "release_date":
                                "2026-09-20",
                        },
                        {
                            "label": "PC",
                            "release_date": None,
                        },
                    ],
                }
            ],
            "sha",
        ),
    )

    result = (
        huginn.build_watchlist_message()
    )

    assert "👀 MI LISTADO DE JUEGOS" in result
    assert "🎮 Test Game" in result
    assert "PS5 — 20-09-2026" in result
    assert "PC — Sin fecha" in result


def test_build_watchlist_message_legacy_format(
    monkeypatch,
):
    # Mantiene compatibilidad con formato antiguo
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [
                {
                    "id": 1,
                    "name": "Old Game",
                    "platforms": [
                        "PS5",
                        "PC",
                    ],
                    "release_date":
                        "2026-10-01",
                }
            ],
            "sha",
        ),
    )

    result = (
        huginn.build_watchlist_message()
    )

    assert "🎮 Old Game" in result

    assert (
        "PS5 | PC — 01-10-2026"
        in result
    )


def test_build_watchlist_message_without_platforms(
    monkeypatch,
):
    # Muestra plataforma pendiente si no existe
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [
                {
                    "id": 1,
                    "name": "Unknown Game",
                    "release_date":
                        "2026-11-01",
                }
            ],
            "sha",
        ),
    )

    result = (
        huginn.build_watchlist_message()
    )

    assert (
        "Plataformas por confirmar "
        "— 01-11-2026"
        in result
    )


# ============================================================
# FECHAS Y NEXT
# ============================================================

def test_parse_release_date():
    # Convierte texto a fecha
    result = huginn.parse_release_date(
        "2026-09-20"
    )

    assert result.isoformat() == "2026-09-20"


def test_parse_release_date_without_date():
    # Devuelve None si no hay fecha
    assert (
        huginn.parse_release_date(None)
        is None
    )


def test_parse_release_date_invalid():
    # Devuelve None si la fecha es inválida
    assert (
        huginn.parse_release_date(
            "invalid-date"
        )
        is None
    )


def test_get_upcoming_games(
    monkeypatch,
):
    # Filtra, ordena y agrupa próximos juegos
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(
                2026,
                9,
                14,
                12,
                0,
                tzinfo=tz,
            )

        @classmethod
        def strptime(cls, value, fmt):
            return datetime.strptime(
                value,
                fmt,
            )

    watchlist = [
        {
            "name": "Game B",
            "platforms": [
                {
                    "label": "PC",
                    "release_date":
                        "2026-09-20",
                },
                {
                    "label": "PS5",
                    "release_date":
                        "2026-09-18",
                },
                {
                    "label": "PS4",
                    "release_date":
                        "2026-09-01",
                },
                {
                    "label": "Xbox",
                    "release_date":
                        "invalid",
                },
            ],
        },
        {
            "name": "Game A",
            "platforms": [
                "PS5",
                "PC",
            ],
            "release_date":
                "2026-09-16",
        },
        {
            "name": "Game C",
            "release_date":
                "2026-09-17",
        },
        {
            "name": "Past Game",
            "release_date":
                "2026-09-01",
        },
    ]

    monkeypatch.setattr(
        huginn,
        "datetime",
        FakeDatetime,
    )

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            watchlist,
            "sha",
        ),
    )

    result = huginn.get_upcoming_games()

    assert [
        game["name"]
        for game in result
    ] == [
        "Game A",
        "Game C",
        "Game B",
    ]

    assert (
        result[0]["releases"][0]["label"]
        == "PS5 | PC"
    )

    assert (
        result[1]["releases"][0]["label"]
        == "Plataformas por confirmar"
    )

    assert [
        release["label"]
        for release
        in result[2]["releases"]
    ] == [
        "PS5",
        "PC",
    ]


def test_get_upcoming_games_limits_results(
    monkeypatch,
):
    # Limita el resultado a cinco juegos
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(
                2026,
                9,
                14,
                tzinfo=tz,
            )

        @classmethod
        def strptime(cls, value, fmt):
            return datetime.strptime(
                value,
                fmt,
            )

    watchlist = [
        {
            "name": f"Game {index}",
            "release_date":
                f"2026-09-{15 + index:02d}",
        }
        for index in range(6)
    ]

    monkeypatch.setattr(
        huginn,
        "datetime",
        FakeDatetime,
    )

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            watchlist,
            "sha",
        ),
    )

    result = huginn.get_upcoming_games()

    assert len(result) == 5

    assert [
        game["name"]
        for game in result
    ] == [
        "Game 0",
        "Game 1",
        "Game 2",
        "Game 3",
        "Game 4",
    ]


def test_build_next_message_empty(
    monkeypatch,
):
    # Informa si no hay próximos juegos
    monkeypatch.setattr(
        huginn,
        "get_upcoming_games",
        lambda: [],
    )

    assert (
        huginn.build_next_message()
        == (
            "⏭️ No tienes próximos "
            "lanzamientos con fecha."
        )
    )


def test_build_next_message(
    monkeypatch,
):
    # Construye la lista de próximos juegos
    monkeypatch.setattr(
        huginn,
        "get_upcoming_games",
        lambda: [
            {
                "name": "Test Game",
                "releases": [
                    {
                        "label": "PS5",
                        "date":
                            "2026-09-20",
                    },
                    {
                        "label": "PC",
                        "date":
                            "2026-09-21",
                    },
                ],
            }
        ],
    )

    result = huginn.build_next_message()

    assert (
        "⏭️ PRÓXIMOS LANZAMIENTOS"
        in result
    )

    assert "🎮 Test Game" in result
    assert "PS5 — 20-09-2026" in result
    assert "PC — 21-09-2026" in result


# ============================================================
# BOTONES
# ============================================================

def test_build_search_keyboard():
    # Construye botones de búsqueda
    games = [
        {
            "id": 123,
            "name": "Game One",
        },
        {
            "id": 456,
            "name": "Game Two",
        },
    ]

    result = huginn.build_search_keyboard(
        games
    )

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text": "Game One",
                    "callback_data":
                        "watch:123",
                }
            ],
            [
                {
                    "text": "Game Two",
                    "callback_data":
                        "watch:456",
                }
            ],
        ]
    }


def test_build_unwatch_keyboard():
    # Construye botones para eliminar juegos
    watchlist = [
        {
            "id": 123,
            "name": "Game One",
        }
    ]

    result = (
        huginn.build_unwatch_keyboard(
            watchlist
        )
    )

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text": "❌ Game One",
                    "callback_data":
                        "unwatch:123",
                }
            ],
        ]
    }


# ============================================================
# WATCHLIST
# ============================================================

def test_add_game_to_watchlist_not_found(
    monkeypatch,
):
    # No añade juegos inexistentes
    monkeypatch.setattr(
        huginn,
        "get_igdb_game",
        lambda game_id: None,
    )

    result = (
        huginn.add_game_to_watchlist(
            999
        )
    )

    assert result == (
        None,
        False,
    )


def test_add_game_to_watchlist_existing(
    monkeypatch,
):
    # No duplica juegos ya guardados
    game = {
        "id": 123,
        "name": "Test Game",
    }

    existing = {
        "id": 123,
        "name": "Test Game",
    }

    monkeypatch.setattr(
        huginn,
        "get_igdb_game",
        lambda game_id: game,
    )

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [existing],
            "sha",
        ),
    )

    result = (
        huginn.add_game_to_watchlist(
            123
        )
    )

    assert result == (
        existing,
        False,
    )


def test_add_game_to_watchlist(
    monkeypatch,
):
    # Guarda un juego nuevo con sus plataformas
    game = {
        "id": 123,
        "name": "Test Game",
        "first_release_date":
            123456789,
    }

    watchlist = []
    saved = {}

    monkeypatch.setattr(
        huginn,
        "get_igdb_game",
        lambda game_id: game,
    )

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            watchlist,
            "test-sha",
        ),
    )

    monkeypatch.setattr(
        huginn,
        "format_release_date",
        lambda timestamp:
            "2026-09-20",
    )

    monkeypatch.setattr(
        huginn,
        "build_platform_data",
        lambda game: [
            {
                "label": "PS5",
                "release_date":
                    "2026-09-20",
            }
        ],
    )

    def fake_save(
        new_watchlist,
        sha,
    ):
        saved["watchlist"] = (
            new_watchlist.copy()
        )
        saved["sha"] = sha

    monkeypatch.setattr(
        huginn,
        "save_watchlist",
        fake_save,
    )

    result, added = (
        huginn.add_game_to_watchlist(
            123
        )
    )

    assert added is True

    assert saved["sha"] == "test-sha"

    assert saved["watchlist"] == [
        {
            "id": 123,
            "name": "Test Game",
            "release_date":
                "2026-09-20",
            "platforms": [
                {
                    "label": "PS5",
                    "release_date":
                        "2026-09-20",
                }
            ],
        }
    ]

    assert (
        result["release_date"]
        == "2026-09-20"
    )

    assert result["platform_data"] == [
        {
            "label": "PS5",
            "release_date":
                "2026-09-20",
        }
    ]


def test_remove_game_from_watchlist_not_found(
    monkeypatch,
):
    # No elimina juegos inexistentes
    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [],
            "sha",
        ),
    )

    result = (
        huginn.remove_game_from_watchlist(
            123
        )
    )

    assert result == (
        None,
        False,
    )


def test_remove_game_from_watchlist(
    monkeypatch,
):
    # Elimina un juego existente
    watchlist = [
        {
            "id": 123,
            "name": "Game One",
        },
        {
            "id": 456,
            "name": "Game Two",
        },
    ]

    saved = {}

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            watchlist,
            "test-sha",
        ),
    )

    def fake_save(
        new_watchlist,
        sha,
    ):
        saved["watchlist"] = (
            new_watchlist
        )
        saved["sha"] = sha

    monkeypatch.setattr(
        huginn,
        "save_watchlist",
        fake_save,
    )

    game, removed = (
        huginn.remove_game_from_watchlist(
            123
        )
    )

    assert removed is True

    assert game == {
        "id": 123,
        "name": "Game One",
    }

    assert saved["watchlist"] == [
        {
            "id": 456,
            "name": "Game Two",
        }
    ]

    assert saved["sha"] == "test-sha"


# ============================================================
# CALLBACKS
# ============================================================

def test_handle_watch_callback_not_found(
    monkeypatch,
):
    # Informa si el juego no existe
    sent = []

    monkeypatch.setattr(
        huginn,
        "add_game_to_watchlist",
        lambda game_id:
            (None, False),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_watch_callback(
        "123",
        999,
    )

    assert sent == [
        (
            "123",
            (
                "❌ No he podido "
                "encontrar el juego."
            ),
        )
    ]


def test_handle_watch_callback_existing(
    monkeypatch,
):
    # Informa si ya estaba guardado
    sent = []

    game = {
        "id": 123,
        "name": "Test Game",
    }

    monkeypatch.setattr(
        huginn,
        "add_game_to_watchlist",
        lambda game_id:
            (game, False),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_watch_callback(
        "123",
        123,
    )

    assert sent == [
        (
            "123",
            (
                "ℹ️ Ese juego ya estaba "
                "en tu lista: Test Game"
            ),
        )
    ]


def test_handle_watch_callback_added(
    monkeypatch,
):
    # Confirma que el juego fue añadido
    sent = []

    game = {
        "id": 123,
        "name": "Test Game",
    }

    monkeypatch.setattr(
        huginn,
        "add_game_to_watchlist",
        lambda game_id:
            (game, True),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_watch_callback(
        "123",
        123,
    )

    assert sent == [
        (
            "123",
            "✅ Añadido: Test Game",
        )
    ]


def test_handle_unwatch_callback_missing(
    monkeypatch,
):
    # Informa si el juego ya no está guardado
    sent = []

    monkeypatch.setattr(
        huginn,
        "remove_game_from_watchlist",
        lambda game_id:
            (None, False),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_unwatch_callback(
        "123",
        123,
    )

    assert sent == [
        (
            "123",
            (
                "ℹ️ Ese juego ya no "
                "está en tu lista."
            ),
        )
    ]


def test_handle_unwatch_callback_removed(
    monkeypatch,
):
    # Confirma que el juego fue eliminado
    sent = []

    game = {
        "id": 123,
        "name": "Test Game",
    }

    monkeypatch.setattr(
        huginn,
        "remove_game_from_watchlist",
        lambda game_id:
            (game, True),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_unwatch_callback(
        "123",
        123,
    )

    assert sent == [
        (
            "123",
            "🗑️ Eliminado: Test Game",
        )
    ]


def test_handle_huginn_callback_unauthorized(
    monkeypatch,
):
    # Ignora callbacks de otros chats
    answered = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id:
            answered.append(callback_id),
    )

    result = (
        huginn.handle_huginn_callback(
            {
                "id": "callback-1",
                "data": "watch:123",
                "message": {
                    "chat": {
                        "id": "999999",
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert answered == []


def test_handle_huginn_callback_watch(
    monkeypatch,
):
    # Procesa callback para añadir juego
    answered = []
    handled = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id:
            answered.append(callback_id),
    )

    monkeypatch.setattr(
        huginn,
        "handle_watch_callback",
        lambda chat_id, game_id:
            handled.append(
                (
                    chat_id,
                    game_id,
                )
            ),
    )

    result = (
        huginn.handle_huginn_callback(
            {
                "id": "callback-1",
                "data": "watch:123",
                "message": {
                    "chat": {
                        "id":
                            huginn.HUGINN_CHAT_ID,
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert answered == [
        "callback-1",
    ]

    assert handled == [
        (
            huginn.HUGINN_CHAT_ID,
            123,
        )
    ]


def test_handle_huginn_callback_unwatch(
    monkeypatch,
):
    # Procesa callback para eliminar juego
    handled = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id: None,
    )

    monkeypatch.setattr(
        huginn,
        "handle_unwatch_callback",
        lambda chat_id, game_id:
            handled.append(
                (
                    chat_id,
                    game_id,
                )
            ),
    )

    result = (
        huginn.handle_huginn_callback(
            {
                "id": "callback-1",
                "data": "unwatch:456",
                "message": {
                    "chat": {
                        "id":
                            huginn.HUGINN_CHAT_ID,
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert handled == [
        (
            huginn.HUGINN_CHAT_ID,
            456,
        )
    ]


def test_handle_huginn_callback_without_id(
    monkeypatch,
):
    # Permite callbacks sin ID
    answered = []

    monkeypatch.setattr(
        huginn,
        "answer_huginn_callback",
        lambda callback_id:
            answered.append(callback_id),
    )

    result = (
        huginn.handle_huginn_callback(
            {
                "data": "unknown",
                "message": {
                    "chat": {
                        "id":
                            huginn.HUGINN_CHAT_ID,
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert answered == []


# ============================================================
# COMANDOS
# ============================================================

def test_handle_huginn_message_unauthorized(
    monkeypatch,
):
    # Ignora mensajes de otros chats
    sent = []

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    result = (
        huginn.handle_huginn_message(
            {
                "chat": {
                    "id": "999999",
                },
                "text": "/help",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == []


def test_handle_huginn_help(
    monkeypatch,
):
    # Responde al comando /help
    sent = []

    monkeypatch.setattr(
        huginn,
        "build_help_message",
        lambda: "HELP",
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    result = (
        huginn.handle_huginn_message(
            {
                "chat": {
                    "id":
                        huginn.HUGINN_CHAT_ID,
                },
                "text": "  /help  ",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "HELP",
        )
    ]


def test_handle_huginn_next(
    monkeypatch,
):
    # Responde al comando /next
    sent = []

    monkeypatch.setattr(
        huginn,
        "build_next_message",
        lambda: "NEXT",
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text": "/next",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "NEXT",
        )
    ]


def test_handle_huginn_watchlist(
    monkeypatch,
):
    # Responde al comando /watchlist
    sent = []

    monkeypatch.setattr(
        huginn,
        "build_watchlist_message",
        lambda: "WATCHLIST",
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text": "/watchlist",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "WATCHLIST",
        )
    ]


def test_handle_huginn_unwatch_empty(
    monkeypatch,
):
    # Informa si no hay juegos para eliminar
    sent = []

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            [],
            "sha",
        ),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text": "/unwatch",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "👀 Tu lista está vacía.",
        )
    ]


def test_handle_huginn_unwatch_with_games(
    monkeypatch,
):
    # Muestra botones para eliminar juegos
    sent = []

    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
        }
    ]

    monkeypatch.setattr(
        huginn,
        "get_watchlist",
        lambda: (
            watchlist,
            "sha",
        ),
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text": "/unwatch",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "¿Qué juego quieres eliminar?",
            {
                "inline_keyboard": [
                    [
                        {
                            "text":
                                "❌ Test Game",
                            "callback_data":
                                "unwatch:123",
                        }
                    ]
                ]
            },
        )
    ]


def test_handle_huginn_watch_without_name(
    monkeypatch,
):
    # Muestra uso correcto de /watch
    sent = []

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text": "/watch",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            (
                "Uso: /watch "
                "nombre del juego"
            ),
        )
    ]


def test_handle_huginn_watch_empty_search(
    monkeypatch,
):
    # Protege búsquedas vacías tras /watch
    sent = []

    class FakeText:
        def strip(self):
            return "/watch "

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    result = (
        huginn.handle_huginn_message(
            {
                "chat": {
                    "id":
                        huginn.HUGINN_CHAT_ID,
                },
                "text": FakeText(),
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            (
                "Uso: /watch "
                "nombre del juego"
            ),
        )
    ]


def test_handle_huginn_watch_not_found(
    monkeypatch,
):
    # Informa si IGDB no encuentra juegos
    sent = []

    monkeypatch.setattr(
        huginn,
        "search_igdb_games",
        lambda search_term: [],
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text":
                "/watch Unknown Game",
        }
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            (
                "❌ No he encontrado "
                "ningún juego."
            ),
        )
    ]


def test_handle_huginn_watch_results(
    monkeypatch,
):
    # Muestra resultados encontrados en IGDB
    sent = []

    games = [
        {
            "id": 123,
            "name": "Test Game",
        }
    ]

    captured = {}

    def fake_search(search_term):
        captured["term"] = search_term

        return games

    monkeypatch.setattr(
        huginn,
        "search_igdb_games",
        fake_search,
    )

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    huginn.handle_huginn_message(
        {
            "chat": {
                "id":
                    huginn.HUGINN_CHAT_ID,
            },
            "text":
                "/watch   Test Game  ",
        }
    )

    assert (
        captured["term"]
        == "Test Game"
    )

    assert sent == [
        (
            huginn.HUGINN_CHAT_ID,
            "¿Qué juego quieres añadir?",
            {
                "inline_keyboard": [
                    [
                        {
                            "text":
                                "Test Game",
                            "callback_data":
                                "watch:123",
                        }
                    ]
                ]
            },
        )
    ]


def test_handle_huginn_unknown_command(
    monkeypatch,
):
    # Ignora comandos desconocidos
    sent = []

    monkeypatch.setattr(
        huginn,
        "send_huginn_message",
        lambda *args:
            sent.append(args),
    )

    result = (
        huginn.handle_huginn_message(
            {
                "chat": {
                    "id":
                        huginn.HUGINN_CHAT_ID,
                },
                "text": "/unknown",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == []


# ============================================================
# ENTRADA
# ============================================================

def test_handle_huginn_update_callback(
    monkeypatch,
):
    # Prioriza callbacks válidos
    callback = {
        "id": "callback-1",
    }

    monkeypatch.setattr(
        huginn,
        "handle_huginn_callback",
        lambda received: {
            "type": "callback",
            "data": received,
        },
    )

    result = (
        huginn.handle_huginn_update(
            {
                "callback_query":
                    callback,
            }
        )
    )

    assert result == {
        "type": "callback",
        "data": callback,
    }


def test_handle_huginn_update_message(
    monkeypatch,
):
    # Procesa mensajes normales
    message = {
        "text": "/help",
    }

    monkeypatch.setattr(
        huginn,
        "handle_huginn_message",
        lambda received: {
            "type": "message",
            "data": received,
        },
    )

    result = (
        huginn.handle_huginn_update(
            {
                "message": message,
            }
        )
    )

    assert result == {
        "type": "message",
        "data": message,
    }


def test_handle_huginn_update_empty():
    # Ignora updates sin contenido útil
    result = (
        huginn.handle_huginn_update(
            {}
        )
    )

    assert result == {
        "ok": True,
    }
