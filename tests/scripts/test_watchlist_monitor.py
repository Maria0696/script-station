import logging
from datetime import UTC, date, datetime

import pytest

from scripts import watchlist_monitor as monitor

# "Hoy" fijo: anterior a todas las fechas de los tests,
# para que no dependan del día en que se ejecutan
TODAY = date(2026, 1, 1)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(monitor, "get_today", lambda: TODAY)


def timestamp(year, month, day):
    return int(datetime(year, month, day, tzinfo=UTC).timestamp())


def test_load_watchlist(monkeypatch):
    data = [{"id": 123, "name": "Test Game"}]

    monkeypatch.setattr(monitor.github, "get_watchlist", lambda: (data, "test-sha"))

    assert monitor.load_watchlist() == (data, "test-sha")


def test_save_watchlist(monkeypatch):
    captured = {}

    def fake_save_watchlist(watchlist, sha, message):
        captured.update(watchlist=watchlist, sha=sha, message=message)

    monkeypatch.setattr(monitor.github, "save_watchlist", fake_save_watchlist)

    data = [{"id": 123, "name": "Test Game"}]

    monitor.save_watchlist(data, "test-sha")

    assert captured == {
        "watchlist": data,
        "sha": "test-sha",
        "message": ("chore: update watchlist release dates"),
    }


def test_send_notification(monkeypatch):
    captured = {}

    def fake_huginn(text, reply_markup=None, parse_mode=None, chat_id=None):
        captured["text"] = text

        captured["reply_markup"] = reply_markup

        captured["parse_mode"] = parse_mode

        captured["chat_id"] = chat_id

        return {"ok": True}

    monkeypatch.setattr(monitor.notifications, "huginn", fake_huginn)

    result = monitor.send_notification("Test message")

    assert result == {"ok": True}

    assert captured["text"] == "Test message"

    assert captured["reply_markup"] is None

    assert captured["parse_mode"] is None

    assert captured["chat_id"] is None


def test_build_change_message_new_date():
    result = monitor.build_change_message("Test Game", "🔵 PS5", None, "2026-09-20")

    assert result == (
        "📅 NUEVA FECHA DE LANZAMIENTO\n\n🎮 Test Game\n🔵 PS5\n📅 20-09-2026"
    )


def test_build_change_message_removed_date():
    result = monitor.build_change_message("Test Game", "🔵 PS5", "2026-09-20", None)

    assert "⚠️ FECHA DE LANZAMIENTO RETIRADA" in result

    assert "Antes: 20-09-2026" in result

    assert "Ahora: Por confirmar" in result


def test_build_change_message_delay():
    result = monitor.build_change_message(
        "Test Game", "🔵 PS5", "2026-09-20", "2026-10-01"
    )

    assert "⏳ RETRASO DE LANZAMIENTO" in result

    assert "Antes: 20-09-2026" in result

    assert "Ahora: 01-10-2026" in result


def test_build_change_message_advance():
    result = monitor.build_change_message(
        "Test Game", "🔵 PS5", "2026-10-01", "2026-09-20"
    )

    assert "⏩ ADELANTO DE LANZAMIENTO" in result


def test_build_change_message_same_date():
    result = monitor.build_change_message(
        "Test Game", "🔵 PS5", "2026-09-20", "2026-09-20"
    )

    assert result is None


def test_monitor_watchlist_empty(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=monitor.__name__)

    monkeypatch.setattr(monitor, "load_watchlist", lambda: ([], None))

    result = monitor.monitor_watchlist()

    output = caplog.text

    assert result is False

    assert "Watchlist is empty." in output


def test_monitor_watchlist_game_not_found(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=monitor.__name__)

    watchlist = [{"id": 123, "name": "Missing Game"}]

    saved = []

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(monitor.igdb, "get_igdb_games", lambda ids: {})

    monkeypatch.setattr(monitor.igdb, "get_release_dates", lambda ids: {})

    monkeypatch.setattr(monitor, "save_watchlist", lambda data, sha: saved.append(data))

    result = monitor.monitor_watchlist()

    output = caplog.text

    assert result is False

    assert saved == []

    assert "Game not found: Missing Game (123)" in output


def test_monitor_watchlist_migrates_old_format(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=monitor.__name__)

    watchlist = [{"id": 123, "name": "Old Game", "platforms": ["PS5", "PC"]}]

    saved = []

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
            123: {
                "id": 123,
                "name": "New Name",
                "first_release_date": timestamp(2026, 9, 20),
                "platforms": [167],
            }
        },
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {123: {167: {"date": "2026-09-20", "precision": "day"}}},
    )

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: saved.append(data.copy())
    )

    result = monitor.monitor_watchlist()

    output = caplog.text

    assert result is True

    assert "Migrated platforms: New Name" in output

    assert len(saved) == 1

    assert watchlist[0]["name"] == "New Name"

    assert watchlist[0]["release_date"] == "2026-09-20"

    assert watchlist[0]["platforms"] == [
        {
            "id": 167,
            "label": "🔵 PS5",
            "release_date": "2026-09-20",
            "date_precision": "day",
        }
    ]


def test_monitor_watchlist_date_changed(monkeypatch):
    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
            "release_date": "2026-09-20",
            "platforms": [
                {
                    "id": 167,
                    "label": "🔵 PS5",
                    "release_date": "2026-09-20",
                    "date_precision": "day",
                }
            ],
        }
    ]

    messages = []
    saved = []

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
            123: {
                "id": 123,
                "name": "Test Game",
                "first_release_date": timestamp(2026, 10, 1),
                "platforms": [167],
            }
        },
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {123: {167: {"date": "2026-10-01", "precision": "day"}}},
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message, reply_markup: messages.append(message),
    )

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: saved.append(data.copy())
    )

    result = monitor.monitor_watchlist()

    assert result is True

    assert len(messages) == 1

    assert len(saved) == 1

    assert "⏳ RETRASO DE LANZAMIENTO" in messages[0]

    assert watchlist[0]["platforms"][0]["release_date"] == "2026-10-01"


def mock_delayed_game(monkeypatch, events):
    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
            "release_date": "2026-09-20",
            "platforms": [
                {
                    "id": 167,
                    "label": "🔵 PS5",
                    "release_date": "2026-09-20",
                    "date_precision": "day",
                }
            ],
        }
    ]

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {123: {"id": 123, "name": "Test Game", "platforms": [167]}},
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {123: {167: {"date": "2026-10-01", "precision": "day"}}},
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message, reply_markup: events.append("notify"),
    )


def test_monitor_watchlist_notifies_after_saving(monkeypatch):
    events = []

    mock_delayed_game(monkeypatch, events)

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: events.append("save")
    )

    monitor.monitor_watchlist()

    assert events == ["save", "notify"]


def test_monitor_watchlist_does_not_notify_if_save_fails(monkeypatch):
    events = []

    mock_delayed_game(monkeypatch, events)

    def failing_save(data, sha):
        raise OSError("GitHub unavailable")

    monkeypatch.setattr(monitor, "save_watchlist", failing_save)

    with pytest.raises(OSError):
        monitor.monitor_watchlist()

    assert events == []


def test_monitor_watchlist_without_changes(monkeypatch):
    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
            "release_date": "2026-09-20",
            "platforms": [
                {
                    "id": 167,
                    "label": "🔵 PS5",
                    "release_date": "2026-09-20",
                    "date_precision": "day",
                }
            ],
        }
    ]

    saved = []
    sent = []

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
            123: {
                "id": 123,
                "name": "Test Game",
                "first_release_date": timestamp(2026, 9, 20),
                "platforms": [167],
            }
        },
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {123: {167: {"date": "2026-09-20", "precision": "day"}}},
    )

    monkeypatch.setattr(monitor, "save_watchlist", lambda data, sha: saved.append(data))

    monkeypatch.setattr(
        monitor, "send_notification", lambda message, reply_markup: sent.append(message)
    )

    result = monitor.monitor_watchlist()

    assert result is False

    assert saved == []

    assert sent == []


def test_monitor_watchlist_platform_change(monkeypatch):
    watchlist = [
        {
            "id": 123,
            "name": "Test Game",
            "platforms": [
                {
                    "id": 167,
                    "label": "🔵 PS5",
                    "release_date": None,
                    "date_precision": None,
                }
            ],
        }
    ]

    saved = []

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {123: {"id": 123, "name": "Test Game", "platforms": [167, 6]}},
    )

    monkeypatch.setattr(monitor.igdb, "get_release_dates", lambda ids: {})

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: saved.append(data.copy())
    )

    result = monitor.monitor_watchlist()

    assert result is True

    assert len(saved) == 1

    assert len(watchlist[0]["platforms"]) == 2


def test_main(monkeypatch):
    called = []

    monkeypatch.setattr(monitor, "monitor_watchlist", lambda: called.append(True))

    monitor.main()

    assert called == [True]


@pytest.mark.parametrize(
    ("old", "new", "title"),
    [
        # "2027" pasa a un día de 2027: se concreta, no se adelanta
        (("2027-12-31", "year"), ("2027-03-15", "day"), "📅 FECHA CONCRETADA"),
        (("2027-12-31", "quarter"), ("2027-11-30", "month"), "📅 FECHA CONCRETADA"),
        (("2027-02-12", "day"), ("2027-12-31", "year"), "⚠️ FECHA MENOS CONCRETA"),
        (("2027-12-31", "year"), ("2028-01-10", "day"), "⏳ RETRASO DE LANZAMIENTO"),
        (
            ("2027-03-31", "quarter"),
            ("2026-12-01", "day"),
            "⏩ ADELANTO DE LANZAMIENTO",
        ),
    ],
)
def test_build_change_message_with_precision(old, new, title):
    message = monitor.build_change_message(
        "Ill", "🔵 PS5", old[0], new[0], old[1], new[1]
    )

    assert message.startswith(title)


def test_build_change_message_shows_precision():
    message = monitor.build_change_message(
        "Ill", "🔵 PS5", "2027-12-31", "2027-03-31", "year", "month"
    )

    assert "Antes: 2027\nAhora: Marzo 2027" in message


def test_build_change_message_same_period_and_precision():
    message = monitor.build_change_message(
        "Ill", "🔵 PS5", "2027-12-30", "2027-12-31", "year", "year"
    )

    assert message is None


def mock_ill(monkeypatch, stored_platform, new_release, events):
    watchlist = [{"id": 142520, "name": "Ill", "platforms": [stored_platform]}]

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {142520: {"id": 142520, "name": "Ill", "platforms": [167]}},
    )

    monkeypatch.setattr(
        monitor.igdb, "get_release_dates", lambda ids: {142520: {167: new_release}}
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message, reply_markup: events.append(message),
    )

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: events.append("save")
    )

    return watchlist


def test_monitor_watchlist_migrates_precision_silently(monkeypatch):
    events = []

    watchlist = mock_ill(
        monkeypatch,
        {"id": 167, "label": "🔵 PS5", "release_date": "2027-12-31"},
        {"date": "2027-12-31", "precision": "year"},
        events,
    )

    assert monitor.monitor_watchlist() is True

    assert events == ["save"]

    assert watchlist[0]["platforms"][0]["date_precision"] == "year"


def test_monitor_watchlist_notifies_concrete_date(monkeypatch):
    events = []

    mock_ill(
        monkeypatch,
        {
            "id": 167,
            "label": "🔵 PS5",
            "release_date": "2027-12-31",
            "date_precision": "year",
        },
        {"date": "2027-03-15", "precision": "day"},
        events,
    )

    monitor.monitor_watchlist()

    assert events[0] == "save"
    assert events[1].startswith("📅 FECHA CONCRETADA")
    assert "Antes: 2027\nAhora: 15-03-2027" in events[1]


real_get_today = monitor.get_today


def test_get_today_uses_madrid_time():
    assert real_get_today() == datetime.now(monitor.MADRID_TZ).date()


def platform(platform_id, release_date, precision="day", **extra):
    labels = {167: "🔵 PS5", 6: "💻 PC"}

    return {
        "id": platform_id,
        "label": labels[platform_id],
        "release_date": release_date,
        "date_precision": precision,
        **extra,
    }


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (platform(167, "2026-01-01"), True),
        (platform(167, "2025-12-31"), True),
        (platform(167, "2026-01-02"), False),
        # Una fecha imprecisa nunca cuenta como salida
        (platform(167, "2025-12-31", "year"), False),
        (platform(167, None, None), False),
        ({"id": 167, "release_date": "2025-12-31"}, True),
    ],
)
def test_is_released(stored, expected):
    assert monitor.is_released(stored, TODAY) is expected


def test_build_release_message_today_with_rating():
    message = monitor.build_release_message(
        "Marvel's Wolverine",
        [platform(167, "2026-01-01")],
        {"aggregated_rating": 87.75, "aggregated_rating_count": 4},
        TODAY,
    )

    assert message == (
        "🎉 ¡SALE HOY!\n\n"
        "🎮 Marvel's Wolverine\n"
        "🔵 PS5 — 01-01-2026\n\n"
        "⭐ Crítica: 88/100 (4 reseñas)"
    )


def test_build_release_message_earlier_without_rating():
    message = monitor.build_release_message(
        "Game", [platform(167, "2025-12-30")], {}, TODAY
    )

    assert message == "🎉 YA DISPONIBLE\n\n🎮 Game\n🔵 PS5 — 30-12-2025"


def test_build_release_message_hides_unreliable_rating():
    # Con menos de 3 reseñas la nota no se muestra
    for game in (
        {"aggregated_rating": 70.2},
        {"aggregated_rating": 70.2, "aggregated_rating_count": 2},
    ):
        message = monitor.build_release_message(
            "Game", [platform(167, "2026-01-01")], game, TODAY
        )

        assert "Crítica" not in message


def mock_game(monkeypatch, stored_platforms, igdb_dates, events, **igdb_fields):
    watchlist = [{"id": 1, "name": "Game", "platforms": stored_platforms}]
    platform_ids = list(igdb_dates)

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    monkeypatch.setattr(
        monitor.igdb,
        "get_igdb_games",
        lambda ids: {
            1: {"id": 1, "name": "Game", "platforms": platform_ids, **igdb_fields}
        },
    )

    monkeypatch.setattr(
        monitor.igdb,
        "get_release_dates",
        lambda ids: {
            1: {
                platform_id: {"date": release_date, "precision": "day"}
                for platform_id, release_date in igdb_dates.items()
            }
        },
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message, reply_markup: events.append(message),
    )

    monkeypatch.setattr(
        monitor, "save_watchlist", lambda data, sha: events.append("save")
    )

    return watchlist


def test_monitor_watchlist_alerts_release_and_archives(monkeypatch):
    events = []

    watchlist = mock_game(
        monkeypatch,
        [platform(167, "2026-01-01")],
        {167: "2026-01-01"},
        events,
        aggregated_rating=90,
        aggregated_rating_count=5,
    )

    assert monitor.monitor_watchlist() is True

    assert events[0] == "save"
    assert events[1].startswith("🎉 ¡SALE HOY!")
    assert "⭐ Crítica: 90/100" in events[1]

    game = watchlist[0]

    assert game["status"] == "released"
    assert game["released_on"] == "2026-01-01"
    assert game["platforms"][0]["release_notified"] is True


def test_monitor_watchlist_alerts_missed_release(monkeypatch):
    events = []

    mock_game(monkeypatch, [platform(167, "2025-12-30")], {167: "2025-12-30"}, events)

    monitor.monitor_watchlist()

    assert events[1].startswith("🎉 YA DISPONIBLE")


def test_monitor_watchlist_archives_old_release_silently(monkeypatch):
    events = []

    watchlist = mock_game(
        monkeypatch, [platform(167, "2025-09-15")], {167: "2025-09-15"}, events
    )

    monitor.monitor_watchlist()

    assert events == ["save"]
    assert watchlist[0]["status"] == "released"


def test_monitor_watchlist_partial_release(monkeypatch):
    events = []

    watchlist = mock_game(
        monkeypatch,
        [platform(167, "2026-01-01"), platform(6, "2026-06-01")],
        {167: "2026-01-01", 6: "2026-06-01"},
        events,
    )

    monitor.monitor_watchlist()

    assert "🔵 PS5" in events[1]
    assert "💻 PC" not in events[1]
    assert "status" not in watchlist[0]


def test_monitor_watchlist_does_not_repeat_release_alert(monkeypatch):
    events = []

    mock_game(
        monkeypatch,
        [platform(167, "2026-01-01", release_notified=True), platform(6, "2026-06-01")],
        {167: "2026-01-01", 6: "2026-06-01"},
        events,
    )

    assert monitor.monitor_watchlist() is False
    assert events == []


def test_monitor_watchlist_skips_archived_games(monkeypatch):
    watchlist = [{"id": 1, "name": "Game", "status": "released", "platforms": []}]

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))

    def fail(ids):
        raise AssertionError("unexpected IGDB call")

    monkeypatch.setattr(monitor.igdb, "get_igdb_games", fail)

    assert monitor.monitor_watchlist() is False


def test_archive_if_released_needs_a_dated_platform():
    item = {"name": "Game", "platforms": [platform(167, None, None)]}

    assert monitor.archive_if_released(item, TODAY) is False
    assert "status" not in item


# ============================================================
# TIENDAS Y NOTA DE LA CRÍTICA
# ============================================================

STEAM = {"type": 13, "url": "https://store.steampowered.com/app/1"}
PLAYSTATION = {"type": 23, "url": "https://store.playstation.com/en-us/concept/2"}
GOG = {"type": 17, "url": "https://www.gog.com/game/3"}


def test_build_store_keyboard_two_per_row():
    keyboard = monitor.build_store_keyboard({"websites": [STEAM, PLAYSTATION, GOG]})

    assert keyboard == {
        "inline_keyboard": [
            [
                {
                    "text": "🛒 PlayStation",
                    "url": "https://store.playstation.com/es-es/concept/2",
                },
                {"text": "🛒 Steam", "url": "https://store.steampowered.com/app/1"},
            ],
            [{"text": "🛒 GOG", "url": "https://www.gog.com/game/3"}],
        ]
    }


def test_build_store_keyboard_without_stores():
    assert monitor.build_store_keyboard({"websites": []}) is None


def test_build_critic_score_line():
    line = monitor.build_critic_score_line(
        {"aggregated_rating": 87.75, "aggregated_rating_count": 12}
    )

    assert line == "⭐ Crítica: 88/100 (12 reseñas)"


def released_item(release_date, **extra):
    return {
        "id": 1,
        "name": "Game",
        "platforms": [platform(167, release_date)],
        **extra,
    }


SCORED = {"aggregated_rating": 81, "aggregated_rating_count": 5}


def test_check_critic_score_after_release():
    item = released_item("2025-12-25")

    message = monitor.check_critic_score(item, SCORED, TODAY)

    assert message == "📊 NOTA DE LA CRÍTICA\n\n🎮 Game\n⭐ Crítica: 81/100 (5 reseñas)"
    assert item["rating_notified"] is True

    # Solo una vez
    assert monitor.check_critic_score(item, SCORED, TODAY) is None


@pytest.mark.parametrize(
    ("item", "igdb_game"),
    [
        # Aún no ha salido
        (released_item("2026-02-01"), SCORED),
        # Fuera del plazo de 14 días
        (released_item("2025-12-17"), SCORED),
        # Sin reseñas suficientes
        (released_item("2025-12-25"), {"aggregated_rating": 81}),
        # Fecha imprecisa: no cuenta como salida
        ({"name": "Game", "platforms": [platform(167, "2025-12-31", "year")]}, SCORED),
    ],
)
def test_check_critic_score_skips(item, igdb_game):
    assert monitor.check_critic_score(item, igdb_game, TODAY) is None


def test_awaiting_critic_score_last_day_of_window():
    assert monitor.awaiting_critic_score(released_item("2025-12-18"), TODAY) is True


def test_monitor_watchlist_release_alert_with_stores_and_score(monkeypatch):
    # El aviso de salida lleva tiendas; con nota, no hay aviso de nota aparte
    sent = []

    watchlist = mock_game(
        monkeypatch,
        [platform(167, "2026-01-01")],
        {167: "2026-01-01"},
        [],
        aggregated_rating=90,
        aggregated_rating_count=5,
        websites=[STEAM],
    )

    monkeypatch.setattr(
        monitor,
        "send_notification",
        lambda message, reply_markup: sent.append((message, reply_markup)),
    )

    monitor.monitor_watchlist()

    assert len(sent) == 1
    message, keyboard = sent[0]

    assert "⭐ Crítica: 90/100 (5 reseñas)" in message
    assert keyboard["inline_keyboard"][0][0]["text"] == "🛒 Steam"
    assert watchlist[0]["rating_notified"] is True


def test_monitor_watchlist_critic_score_for_archived_game(monkeypatch):
    # Archivado hace 5 días: se consulta solo para avisar de la nota
    sent = []
    saved = []

    watchlist = [
        released_item("2025-12-27", status="released", released_on="2025-12-27"),
        # Archivado hace meses: no se consulta
        {
            "id": 2,
            "name": "Old",
            "status": "released",
            "platforms": [platform(167, "2025-09-15")],
        },
    ]

    queried = []

    def fake_games(ids):
        queried.append(ids)

        return {1: {"id": 1, "name": "Game", **SCORED}}

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))
    monkeypatch.setattr(monitor.igdb, "get_igdb_games", fake_games)
    monkeypatch.setattr(monitor.igdb, "get_release_dates", lambda ids: {})
    monkeypatch.setattr(monitor, "save_watchlist", lambda data, sha: saved.append(True))
    monkeypatch.setattr(
        monitor, "send_notification", lambda message, reply_markup: sent.append(message)
    )

    assert monitor.monitor_watchlist() is True

    assert queried == [[1]]
    assert saved == [True]
    assert sent[0].startswith("📊 NOTA DE LA CRÍTICA")
    assert watchlist[0]["rating_notified"] is True


def test_monitor_watchlist_archived_game_missing_in_igdb(monkeypatch):
    watchlist = [released_item("2025-12-27", status="released")]

    monkeypatch.setattr(monitor, "load_watchlist", lambda: (watchlist, "sha"))
    monkeypatch.setattr(monitor.igdb, "get_igdb_games", lambda ids: {})
    monkeypatch.setattr(monitor.igdb, "get_release_dates", lambda ids: {})

    assert monitor.monitor_watchlist() is False


def test_monitor_watchlist_critic_score_for_active_game(monkeypatch):
    # Salió en PS5 hace días (ya avisado) y la nota llega hoy;
    # PC sigue pendiente, así que el juego no está archivado
    sent = []

    mock_game(
        monkeypatch,
        [platform(167, "2025-12-28", release_notified=True), platform(6, "2026-06-01")],
        {167: "2025-12-28", 6: "2026-06-01"},
        [],
        **SCORED,
    )

    monkeypatch.setattr(
        monitor, "send_notification", lambda message, reply_markup: sent.append(message)
    )

    assert monitor.monitor_watchlist() is True
    assert sent == ["📊 NOTA DE LA CRÍTICA\n\n🎮 Game\n⭐ Crítica: 81/100 (5 reseñas)"]
