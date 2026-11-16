import logging
from datetime import UTC
from datetime import datetime as real_datetime

from scripts import video_game_releases as releases


def test_get_releases_today(monkeypatch):
    captured = {}

    class FakeDatetime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 14, 12, 0, tzinfo=tz)

    def fake_get_releases_between(start_timestamp, end_timestamp):
        captured.update(start=start_timestamp, end=end_timestamp)

        return [{"game": {"id": 123, "name": "Test Game"}, "platform": 167}]

    monkeypatch.setattr(releases, "datetime", FakeDatetime)

    monkeypatch.setattr(
        releases.igdb, "get_releases_between", fake_get_releases_between
    )

    monkeypatch.setattr(
        releases,
        "filter_and_group_releases",
        lambda values: [
            {"id": value["game"]["id"], "name": value["game"]["name"]}
            for value in values
        ],
    )

    result = releases.get_releases_today()

    assert result == [{"id": 123, "name": "Test Game"}]

    # Día completo de Madrid (UTC+2 en septiembre)
    assert captured == {
        "start": int(real_datetime(2026, 9, 13, 22, 0, tzinfo=UTC).timestamp()),
        "end": int(real_datetime(2026, 9, 14, 22, 0, tzinfo=UTC).timestamp()),
    }


def test_filter_and_group_releases():
    data = [
        {
            "game": {"id": 1, "name": "Game One"},
            "platform": 167,
            "release_region": {"region": "europe"},
        },
        {
            "game": {"id": 1, "name": "Game One"},
            "platform": 6,
            "release_region": {"region": "worldwide"},
        },
        {"game": {"id": 1, "name": "Game One"}, "platform": 167},
        {
            "game": {"id": 2, "name": "Japan Game"},
            "platform": 167,
            "release_region": {"region": "japan"},
        },
        {"game": None, "platform": 167},
        {"game": {"id": None, "name": "Invalid"}, "platform": 167},
        {"game": {"id": 3, "name": None}, "platform": 167},
        {"game": {"id": 4, "name": "Unknown Platform"}, "platform": 999999},
    ]

    result = releases.filter_and_group_releases(data)

    assert len(result) == 1

    assert result[0]["id"] == 1

    assert result[0]["name"] == "Game One"

    assert result[0]["platforms"] == {167, 6}

    assert result[0]["visits"] == 0.0

    assert result[0]["want_to_play"] == 0.0

    assert result[0]["popularity_score"] == 0.0

    assert result[0]["featured"] is False


def test_add_popularity_data_empty():
    assert releases.add_popularity_data([]) == []


def test_add_popularity_data(monkeypatch):
    games = [
        {
            "id": 1,
            "name": "Game One",
            "visits": 0.0,
            "want_to_play": 0.0,
            "popularity_score": 0.0,
        },
        {
            "id": 2,
            "name": "Game Two",
            "visits": 0.0,
            "want_to_play": 0.0,
            "popularity_score": 0.0,
        },
    ]

    popularity_data = [
        {"game_id": 1, "popularity_type": releases.POPULARITY_VISITS, "value": 0.2},
        {
            "game_id": 1,
            "popularity_type": releases.POPULARITY_WANT_TO_PLAY,
            "value": 0.4,
        },
        {"game_id": 2, "popularity_type": releases.POPULARITY_VISITS, "value": None},
        {"game_id": 999, "popularity_type": releases.POPULARITY_VISITS, "value": 10},
        {"game_id": 2, "popularity_type": 999, "value": 10},
    ]

    captured = {}

    def fake_get_popularity_primitives(game_ids, popularity_types):
        captured.update(game_ids=game_ids, popularity_types=popularity_types)

        return popularity_data

    monkeypatch.setattr(
        releases.igdb, "get_popularity_primitives", fake_get_popularity_primitives
    )

    result = releases.add_popularity_data(games)

    assert captured == {
        "game_ids": [1, 2],
        "popularity_types": [
            releases.POPULARITY_VISITS,
            releases.POPULARITY_WANT_TO_PLAY,
        ],
    }

    assert result[0]["visits"] == 0.2

    assert result[0]["want_to_play"] == 0.4

    expected_score = 0.2 * releases.VISITS_WEIGHT + 0.4 * releases.WANT_TO_PLAY_WEIGHT

    assert result[0]["popularity_score"] == expected_score

    assert result[1]["visits"] == 0.0

    assert result[1]["want_to_play"] == 0.0

    assert result[1]["popularity_score"] == 0.0


def test_mark_featured_games_empty():
    assert releases.mark_featured_games([]) == []


def test_mark_featured_games(monkeypatch):
    monkeypatch.setattr(releases, "FEATURED_SCORE_MIN", 0)

    games = [
        {"name": "Alpha", "popularity_score": 100, "featured": False},
        {"name": "Bravo", "popularity_score": 90, "featured": False},
        {"name": "Charlie", "popularity_score": 80, "featured": False},
        {"name": "Delta", "popularity_score": 76, "featured": False},
        {"name": "Echo", "popularity_score": 20, "featured": False},
    ]

    result = releases.mark_featured_games(games)

    featured = [game["name"] for game in result if game["featured"]]

    assert featured == ["Alpha", "Bravo", "Charlie"]

    assert len(featured) == releases.MAX_FEATURED_GAMES


def test_mark_featured_games_debug(caplog):
    caplog.set_level(logging.DEBUG, logger=releases.__name__)

    games = [{"name": "Test Game", "popularity_score": 0.001, "featured": False}]

    releases.mark_featured_games(games)

    output = caplog.text

    assert "PopScore data:" in output

    assert "Test Game" in output

    assert "Score:" in output

    assert "Featured threshold:" in output

    assert "Featured games:" in output


def test_mark_featured_games_without_debug(caplog):
    caplog.set_level(logging.INFO, logger=releases.__name__)

    games = [{"name": "Test Game", "popularity_score": 0.001, "featured": False}]

    releases.mark_featured_games(games)

    assert "Featured games:" in caplog.text

    assert "PopScore data:" not in caplog.text


def test_get_platform_labels():
    result = releases.get_platform_labels({6, 167, 471, 386})

    assert result == ["🔵 PS5", "💻 PC", "🥽 Meta Quest"]


def test_build_messages_without_games(monkeypatch):
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return real_datetime(2026, 9, 14, tzinfo=tz)

    monkeypatch.setattr(releases, "datetime", FakeDatetime)

    result = releases.build_messages([])

    assert len(result) == 1

    assert "NEW GAMES OUT TODAY" in result[0]

    assert "14-09-2026" in result[0]

    assert "No releases found today." in result[0]


def test_build_messages(monkeypatch):
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return real_datetime(2026, 9, 14, tzinfo=tz)

    monkeypatch.setattr(releases, "datetime", FakeDatetime)

    games = [
        {"name": "Game <One>", "platforms": {167, 6}, "featured": True},
        {"name": "Game Two", "platforms": {508}, "featured": False},
    ]

    result = releases.build_messages(games)

    assert len(result) == 1

    message = result[0]

    assert "⭐ <b>Game &lt;One&gt;</b>" in message

    assert "🔵 PS5 | 💻 PC" in message

    assert "<b>Game Two</b>" in message

    assert "🔴 Switch 2" in message


def test_build_messages_splits_long_messages(monkeypatch):
    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return real_datetime(2026, 9, 14, tzinfo=tz)

    monkeypatch.setattr(releases, "datetime", FakeDatetime)

    monkeypatch.setattr(releases, "MAX_TELEGRAM_LENGTH", 300)

    games = [
        {"name": "Game One", "platforms": {167}, "featured": False},
        {"name": "X" * 200, "platforms": {6}, "featured": False},
    ]

    result = releases.build_messages(games)

    assert len(result) == 2

    assert "Game One" in result[0]

    assert "X" * 200 in result[1]


def test_send_notification(monkeypatch):
    captured = {}

    def fake_huginn(text, reply_markup=None, parse_mode=None, chat_id=None):
        captured["text"] = text

        captured["reply_markup"] = reply_markup

        captured["parse_mode"] = parse_mode

        captured["chat_id"] = chat_id

        return {"ok": True}

    monkeypatch.setattr(releases.notifications, "huginn", fake_huginn)

    result = releases.send_notification("Hello Huginn")

    assert result == {"ok": True}

    assert captured["text"] == "Hello Huginn"

    assert captured["reply_markup"] is None

    assert captured["parse_mode"] == "HTML"

    assert captured["chat_id"] is None


def test_main(monkeypatch):
    calls = []

    monkeypatch.setattr(
        releases,
        "get_releases_today",
        lambda: (
            calls.append("releases") or [{"id": 1, "name": "Star", "featured": True}]
        ),
    )

    monkeypatch.setattr(
        releases,
        "add_popularity_data",
        lambda games: calls.append("popularity") or games,
    )

    monkeypatch.setattr(
        releases, "mark_featured_games", lambda games: calls.append("featured") or games
    )

    monkeypatch.setattr(
        releases,
        "build_messages",
        lambda games: calls.append("messages") or ["Message 1", "Message 2"],
    )

    monkeypatch.setattr(
        releases,
        "send_notification",
        lambda message, reply_markup: calls.append(
            (f"send:{message}", bool(reply_markup))
        ),
    )

    releases.main()

    # Los botones "👀 Seguir" solo van en el primer mensaje
    assert calls == [
        "releases",
        "popularity",
        "featured",
        "messages",
        ("send:Message 1", True),
        ("send:Message 2", False),
    ]


def test_build_follow_keyboard_only_featured():
    games = [
        {"id": 1, "name": "Star", "featured": True},
        {"id": 2, "name": "Other", "featured": False},
    ]

    assert releases.build_follow_keyboard(games) == {
        "inline_keyboard": [[{"text": "👀 Seguir Star", "callback_data": "watch:1"}]]
    }


def test_build_follow_keyboard_without_featured():
    assert releases.build_follow_keyboard([{"id": 2, "featured": False}]) is None
