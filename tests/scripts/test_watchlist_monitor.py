from datetime import (
    UTC,
    datetime,
)

import pytest

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
            tzinfo=UTC,
        ).timestamp()
    )


# ============================================================
# WATCHLIST EN GITHUB
# ============================================================

def test_load_watchlist(
    monkeypatch,
):
    data = [
        {
            "id": 123,
            "name":
                "Test Game",
        }
    ]

    monkeypatch.setattr(
        monitor.github,
        "get_watchlist",
        lambda: (
            data,
            "test-sha",
        ),
    )

    assert (
        monitor.load_watchlist()
        == (
            data,
            "test-sha",
        )
    )


def test_save_watchlist(
    monkeypatch,
):
    captured = {}

    def fake_save_watchlist(
        watchlist,
        sha,
        message,
    ):
        captured.update(
            watchlist=watchlist,
            sha=sha,
            message=message,
        )

    monkeypatch.setattr(
        monitor.github,
        "save_watchlist",
        fake_save_watchlist,
    )

    data = [
        {
            "id": 123,
            "name":
                "Test Game",
        }
    ]

    monitor.save_watchlist(
        data,
        "test-sha",
    )

    assert captured == {
        "watchlist": data,
        "sha": "test-sha",
        "message": (
            "chore: update watchlist "
            "release dates"
        ),
    }


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
        lambda:
            ([], None),
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
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids:
            {},
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids:
            {},
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data, sha:
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
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
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
        monitor.igdb,
        "get_release_dates",
        lambda ids: {
            123: {
                167:
                    "2026-09-20",
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data, sha:
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
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
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
        monitor.igdb,
        "get_release_dates",
        lambda ids: {
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
        lambda data, sha:
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


def mock_delayed_game(
    monkeypatch,
    events,
):
    # Juego cuya fecha pasa del 20-09 al 01-10
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

    monkeypatch.setattr(
        monitor,
        "load_watchlist",
        lambda:
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
            123: {
                "id": 123,
                "name":
                    "Test Game",
                "platforms": [
                    167,
                ],
            }
        },
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {
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
            events.append(
                "notify"
            ),
    )


def test_monitor_watchlist_notifies_after_saving(
    monkeypatch,
):
    events = []

    mock_delayed_game(
        monkeypatch,
        events,
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data, sha:
            events.append(
                "save"
            ),
    )

    monitor.monitor_watchlist()

    assert events == [
        "save",
        "notify",
    ]


def test_monitor_watchlist_does_not_notify_if_save_fails(
    monkeypatch,
):
    events = []

    mock_delayed_game(
        monkeypatch,
        events,
    )

    def failing_save(
        data,
        sha,
    ):
        raise OSError(
            "GitHub unavailable"
        )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        failing_save,
    )

    with pytest.raises(OSError):
        monitor.monitor_watchlist()

    assert events == []


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
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
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
        monitor.igdb,
        "get_release_dates",
        lambda ids: {
            123: {
                167:
                    "2026-09-20",
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data, sha:
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
            (watchlist, "sha"),
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
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
        monitor.igdb,
        "get_release_dates",
        lambda ids:
            {},
    )

    monkeypatch.setattr(
        monitor,
        "save_watchlist",
        lambda data, sha:
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
