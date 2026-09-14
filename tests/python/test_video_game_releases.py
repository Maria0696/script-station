from datetime import (
    datetime as real_datetime,
)

from scripts import (
    video_game_releases as releases,
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
        captured[
            "url"
        ] = url

        captured[
            "params"
        ] = params

        captured[
            "timeout"
        ] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        releases.requests,
        "post",
        fake_post,
    )

    result = (
        releases
        .get_access_token()
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
            releases.CLIENT_ID,
        "client_secret":
            releases.CLIENT_SECRET,
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
        releases.get_igdb_headers(
            "test-token"
        )
    )

    assert result == {
        "Client-ID":
            releases.CLIENT_ID,
        "Authorization":
            "Bearer test-token",
        "Accept":
            "application/json",
    }


# ============================================================
# LANZAMIENTOS
# ============================================================

def test_get_releases_today(
    monkeypatch,
):
    captured = {}

    class FakeDatetime(
        real_datetime
    ):
        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return cls(
                2026,
                9,
                14,
                12,
                0,
                tzinfo=tz,
            )

    class FakeResponse:
        ok = True

        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return [
                {
                    "game": {
                        "id": 123,
                        "name":
                            "Test Game",
                    },
                    "platform":
                        167,
                }
            ]

    def fake_post(
        url,
        headers=None,
        data=None,
        timeout=None,
    ):
        captured[
            "url"
        ] = url

        captured[
            "headers"
        ] = headers

        captured[
            "query"
        ] = data

        captured[
            "timeout"
        ] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        releases,
        "datetime",
        FakeDatetime,
    )

    monkeypatch.setattr(
        releases.requests,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        releases,
        "filter_and_group_releases",
        lambda values: [
            {
                "id": 123,
                "name":
                    "Test Game",
            }
        ],
    )

    result = (
        releases
        .get_releases_today(
            "test-token"
        )
    )

    assert result == [
        {
            "id": 123,
            "name":
                "Test Game",
        }
    ]

    assert (
        captured["url"]
        == (
            "https://api.igdb.com/"
            "v4/release_dates"
        )
    )

    assert (
        captured["headers"]
        == releases.get_igdb_headers(
            "test-token"
        )
    )

    assert (
        "where date >="
        in captured["query"]
    )

    assert (
        "platform = ("
        in captured["query"]
    )

    assert (
        "limit 500;"
        in captured["query"]
    )

    assert (
        captured["timeout"]
        == 30
    )


def test_get_releases_today_logs_error(
    monkeypatch,
    capsys,
):
    class FakeDatetime(
        real_datetime
    ):
        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return cls(
                2026,
                9,
                14,
                12,
                tzinfo=tz,
            )

    class FakeResponse:
        ok = False
        status_code = 500
        text = "Server error"

        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return []

    monkeypatch.setattr(
        releases,
        "datetime",
        FakeDatetime,
    )

    monkeypatch.setattr(
        releases.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(),
    )

    result = (
        releases
        .get_releases_today(
            "test-token"
        )
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert result == []

    assert (
        "IGDB releases error: 500"
        in output
    )

    assert (
        "Server error"
        in output
    )


# ============================================================
# FILTRADO
# ============================================================

def test_filter_and_group_releases():
    data = [
        {
            "game": {
                "id": 1,
                "name":
                    "Game One",
            },
            "platform":
                167,
            "release_region": {
                "region":
                    "europe",
            },
        },
        {
            "game": {
                "id": 1,
                "name":
                    "Game One",
            },
            "platform":
                6,
            "release_region": {
                "region":
                    "worldwide",
            },
        },
        {
            "game": {
                "id": 1,
                "name":
                    "Game One",
            },
            "platform":
                167,
        },
        {
            "game": {
                "id": 2,
                "name":
                    "Japan Game",
            },
            "platform":
                167,
            "release_region": {
                "region":
                    "japan",
            },
        },
        {
            "game": None,
            "platform":
                167,
        },
        {
            "game": {
                "id": None,
                "name":
                    "Invalid",
            },
            "platform":
                167,
        },
        {
            "game": {
                "id": 3,
                "name": None,
            },
            "platform":
                167,
        },
        {
            "game": {
                "id": 4,
                "name":
                    "Unknown Platform",
            },
            "platform":
                999999,
        },
    ]

    result = (
        releases
        .filter_and_group_releases(
            data
        )
    )

    assert (
        len(result)
        == 1
    )

    assert (
        result[0]["id"]
        == 1
    )

    assert (
        result[0]["name"]
        == "Game One"
    )

    assert (
        result[0]["platforms"]
        == {
            167,
            6,
        }
    )

    assert (
        result[0]["visits"]
        == 0.0
    )

    assert (
        result[0]["want_to_play"]
        == 0.0
    )

    assert (
        result[0][
            "popularity_score"
        ]
        == 0.0
    )

    assert (
        result[0]["featured"]
        is False
    )


# ============================================================
# POPULARIDAD
# ============================================================

def test_add_popularity_data_empty():
    assert (
        releases
        .add_popularity_data(
            "token",
            [],
        )
        == []
    )


def test_add_popularity_data(
    monkeypatch,
):
    games = [
        {
            "id": 1,
            "name":
                "Game One",
            "visits": 0.0,
            "want_to_play":
                0.0,
            "popularity_score":
                0.0,
        },
        {
            "id": 2,
            "name":
                "Game Two",
            "visits": 0.0,
            "want_to_play":
                0.0,
            "popularity_score":
                0.0,
        },
    ]

    class FakeResponse:
        ok = True

        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return [
                {
                    "game_id":
                        1,
                    "popularity_type":
                        releases
                        .POPULARITY_VISITS,
                    "value":
                        0.2,
                },
                {
                    "game_id":
                        1,
                    "popularity_type":
                        releases
                        .POPULARITY_WANT_TO_PLAY,
                    "value":
                        0.4,
                },
                {
                    "game_id":
                        2,
                    "popularity_type":
                        releases
                        .POPULARITY_VISITS,
                    "value":
                        None,
                },
                {
                    "game_id":
                        999,
                    "popularity_type":
                        releases
                        .POPULARITY_VISITS,
                    "value":
                        10,
                },
                {
                    "game_id":
                        2,
                    "popularity_type":
                        999,
                    "value":
                        10,
                },
            ]

    monkeypatch.setattr(
        releases.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(),
    )

    result = (
        releases
        .add_popularity_data(
            "test-token",
            games,
        )
    )

    assert (
        result[0]["visits"]
        == 0.2
    )

    assert (
        result[0][
            "want_to_play"
        ]
        == 0.4
    )

    expected_score = (
        0.2
        * releases
        .VISITS_WEIGHT
        + 0.4
        * releases
        .WANT_TO_PLAY_WEIGHT
    )

    assert (
        result[0][
            "popularity_score"
        ]
        == expected_score
    )

    assert (
        result[1]["visits"]
        == 0.0
    )

    assert (
        result[1][
            "want_to_play"
        ]
        == 0.0
    )

    assert (
        result[1][
            "popularity_score"
        ]
        == 0.0
    )


def test_add_popularity_data_logs_error(
    monkeypatch,
    capsys,
):
    games = [
        {
            "id": 1,
            "name":
                "Test Game",
            "visits": 0.0,
            "want_to_play":
                0.0,
            "popularity_score":
                0.0,
        }
    ]

    class FakeResponse:
        ok = False
        status_code = 500
        text = (
            "Popularity error"
        )

        def raise_for_status(
            self,
        ):
            pass

        def json(self):
            return []

    monkeypatch.setattr(
        releases.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(),
    )

    releases.add_popularity_data(
        "test-token",
        games,
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "IGDB popularity error: 500"
        in output
    )

    assert (
        "Popularity error"
        in output
    )


# ============================================================
# DESTACADOS
# ============================================================

def test_mark_featured_games_empty():
    assert (
        releases
        .mark_featured_games(
            []
        )
        == []
    )


def test_mark_featured_games(
    monkeypatch,
):
    monkeypatch.setattr(
        releases,
        "FEATURED_SCORE_MIN",
        0,
    )

    games = [
        {
            "name": "Alpha",
            "popularity_score":
                100,
            "featured":
                False,
        },
        {
            "name": "Bravo",
            "popularity_score":
                90,
            "featured":
                False,
        },
        {
            "name": "Charlie",
            "popularity_score":
                80,
            "featured":
                False,
        },
        {
            "name": "Delta",
            "popularity_score":
                76,
            "featured":
                False,
        },
        {
            "name": "Echo",
            "popularity_score":
                20,
            "featured":
                False,
        },
    ]

    result = (
        releases
        .mark_featured_games(
            games
        )
    )

    featured = [
        game["name"]
        for game in result
        if game[
            "featured"
        ]
    ]

    assert featured == [
        "Alpha",
        "Bravo",
        "Charlie",
    ]

    assert (
        len(featured)
        == releases
        .MAX_FEATURED_GAMES
    )


def test_mark_featured_games_debug(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        releases,
        "DEBUG",
        True,
    )

    games = [
        {
            "name":
                "Test Game",
            "popularity_score":
                0.001,
            "featured":
                False,
        }
    ]

    releases.mark_featured_games(
        games
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "PopScore data:"
        in output
    )

    assert (
        "Test Game"
        in output
    )

    assert (
        "Score:"
        in output
    )

    assert (
        "Featured threshold:"
        in output
    )

    assert (
        "Featured games:"
        in output
    )


# ============================================================
# PLATAFORMAS
# ============================================================

def test_get_platform_labels():
    result = (
        releases
        .get_platform_labels(
            {
                6,
                167,
                471,
                386,
            }
        )
    )

    assert result == [
        "🔵 PS5",
        "💻 PC",
        "🥽 Meta Quest",
    ]


# ============================================================
# MENSAJES
# ============================================================

def test_build_messages_without_games(
    monkeypatch,
):
    class FakeDatetime:
        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return real_datetime(
                2026,
                9,
                14,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        releases,
        "datetime",
        FakeDatetime,
    )

    result = (
        releases
        .build_messages([])
    )

    assert (
        len(result)
        == 1
    )

    assert (
        "NEW GAMES OUT TODAY"
        in result[0]
    )

    assert (
        "14-09-2026"
        in result[0]
    )

    assert (
        "No releases found today."
        in result[0]
    )


def test_build_messages(
    monkeypatch,
):
    class FakeDatetime:
        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return real_datetime(
                2026,
                9,
                14,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        releases,
        "datetime",
        FakeDatetime,
    )

    games = [
        {
            "name":
                "Game <One>",
            "platforms": {
                167,
                6,
            },
            "featured":
                True,
        },
        {
            "name":
                "Game Two",
            "platforms": {
                508,
            },
            "featured":
                False,
        },
    ]

    result = (
        releases
        .build_messages(
            games
        )
    )

    assert (
        len(result)
        == 1
    )

    message = result[0]

    assert (
        "⭐ <b>Game &lt;One&gt;</b>"
        in message
    )

    assert (
        "🔵 PS5 | 💻 PC"
        in message
    )

    assert (
        "<b>Game Two</b>"
        in message
    )

    assert (
        "🔴 Switch 2"
        in message
    )


def test_build_messages_splits_long_messages(
    monkeypatch,
):
    class FakeDatetime:
        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return real_datetime(
                2026,
                9,
                14,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        releases,
        "datetime",
        FakeDatetime,
    )

    monkeypatch.setattr(
        releases,
        "MAX_TELEGRAM_LENGTH",
        300,
    )

    games = [
        {
            "name":
                "Game One",
            "platforms": {
                167,
            },
            "featured":
                False,
        },
        {
            "name":
                "X" * 200,
            "platforms": {
                6,
            },
            "featured":
                False,
        },
    ]

    result = (
        releases
        .build_messages(
            games
        )
    )

    assert (
        len(result)
        == 2
    )

    assert (
        "Game One"
        in result[0]
    )

    assert (
        "X" * 200
        in result[1]
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
        releases.notifications,
        "huginn",
        fake_huginn,
    )

    result = (
        releases
        .send_notification(
            "Hello Huginn"
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured["text"]
        == "Hello Huginn"
    )

    assert (
        captured[
            "reply_markup"
        ]
        is None
    )

    assert (
        captured[
            "parse_mode"
        ]
        == "HTML"
    )

    assert (
        captured["chat_id"]
        is None
    )


# ============================================================
# MAIN
# ============================================================

def test_main(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        releases,
        "get_access_token",
        lambda: (
            calls.append(
                "token"
            )
            or "test-token"
        ),
    )

    monkeypatch.setattr(
        releases,
        "get_releases_today",
        lambda token: (
            calls.append(
                "releases"
            )
            or [
                {
                    "id": 1,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        releases,
        "add_popularity_data",
        lambda token, games: (
            calls.append(
                "popularity"
            )
            or games
        ),
    )

    monkeypatch.setattr(
        releases,
        "mark_featured_games",
        lambda games: (
            calls.append(
                "featured"
            )
            or games
        ),
    )

    monkeypatch.setattr(
        releases,
        "build_messages",
        lambda games: (
            calls.append(
                "messages"
            )
            or [
                "Message 1",
                "Message 2",
            ]
        ),
    )

    monkeypatch.setattr(
        releases,
        "send_notification",
        lambda message:
            calls.append(
                f"send:{message}"
            ),
    )

    releases.main()

    assert calls == [
        "token",
        "releases",
        "popularity",
        "featured",
        "messages",
        "send:Message 1",
        "send:Message 2",
    ]
