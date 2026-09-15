import json

from core import telegram

# ============================================================
# TELEGRAM API
# ============================================================

def test_telegram_api(
    monkeypatch,
):
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
            return b'{"ok": true}'

    def fake_urlopen(
        req,
        timeout,
    ):
        captured[
            "request"
        ] = req

        captured[
            "timeout"
        ] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        telegram.request,
        "urlopen",
        fake_urlopen,
    )

    result = telegram.telegram_api(
        "test-token",
        "sendMessage",
        {
            "chat_id": "123",
            "text": "Hello",
        },
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured["timeout"]
        == 30
    )

    assert (
        captured[
            "request"
        ].full_url
        == (
            "https://api.telegram.org/"
            "bottest-token/sendMessage"
        )
    )

    assert (
        captured[
            "request"
        ].get_method()
        == "POST"
    )

    assert json.loads(
        captured[
            "request"
        ].data
    ) == {
        "chat_id": "123",
        "text": "Hello",
    }

    headers = {
        key.lower():
            value
        for key, value
        in captured[
            "request"
        ].header_items()
    }

    assert (
        headers[
            "content-type"
        ]
        == "application/json"
    )


# ============================================================
# SEND MESSAGE
# ============================================================

def test_send_message_with_parse_mode(
    monkeypatch,
):
    captured = {}

    def fake_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_api,
    )

    keyboard = {
        "inline_keyboard": [],
    }

    result = (
        telegram.send_message(
            "token",
            "123",
            "<b>Hello</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    )

    assert result == {
        "ok": True,
    }

    assert captured[
        "data"
    ] == {
        "chat_id":
            "123",
        "text":
            "<b>Hello</b>",
        "reply_markup":
            keyboard,
        "parse_mode":
            "HTML",
    }


# ============================================================
# HUGINN
# ============================================================

def test_send_huginn_message_without_markup(
    monkeypatch,
):
    captured = {}

    def fake_telegram_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_telegram_api,
    )

    result = (
        telegram
        .send_huginn_message(
            "123",
            "Hello Huginn",
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured[
            "bot_token"
        ]
        == telegram.HUGINN_BOT_TOKEN
    )

    assert (
        captured[
            "method"
        ]
        == "sendMessage"
    )

    assert captured[
        "data"
    ] == {
        "chat_id":
            "123",
        "text":
            "Hello Huginn",
    }


def test_send_huginn_message_with_markup(
    monkeypatch,
):
    captured = {}

    keyboard = {
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
    }

    def fake_telegram_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_telegram_api,
    )

    result = (
        telegram
        .send_huginn_message(
            "123",
            "Choose a game",
            keyboard,
        )
    )

    assert result == {
        "ok": True,
    }

    assert captured[
        "data"
    ] == {
        "chat_id":
            "123",
        "text":
            "Choose a game",
        "reply_markup":
            keyboard,
    }


# ============================================================
# HEIMDALL
# ============================================================

def test_send_heimdall_message(
    monkeypatch,
):
    captured = {}

    def fake_telegram_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_telegram_api,
    )

    result = (
        telegram
        .send_heimdall_message(
            "456",
            "Workflow failed",
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured[
            "bot_token"
        ]
        == (
            telegram
            .HEIMDALL_BOT_TOKEN
        )
    )

    assert (
        captured[
            "method"
        ]
        == "sendMessage"
    )

    assert captured[
        "data"
    ] == {
        "chat_id":
            "456",
        "text":
            "Workflow failed",
    }


# ============================================================
# CALLBACKS
# ============================================================

def test_answer_huginn_callback(
    monkeypatch,
):
    captured = {}

    def fake_telegram_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_telegram_api,
    )

    result = (
        telegram
        .answer_huginn_callback(
            "callback-123"
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured[
            "bot_token"
        ]
        == telegram.HUGINN_BOT_TOKEN
    )

    assert (
        captured[
            "method"
        ]
        == "answerCallbackQuery"
    )

    assert captured[
        "data"
    ] == {
        "callback_query_id":
            "callback-123",
    }


def test_answer_heimdall_callback(
    monkeypatch,
):
    captured = {}

    def fake_telegram_api(
        bot_token,
        method,
        data,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "method"
        ] = method

        captured[
            "data"
        ] = data

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        telegram,
        "telegram_api",
        fake_telegram_api,
    )

    result = (
        telegram
        .answer_heimdall_callback(
            "callback-1",
            "Done",
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured[
            "bot_token"
        ]
        == (
            telegram
            .HEIMDALL_BOT_TOKEN
        )
    )

    assert (
        captured[
            "method"
        ]
        == "answerCallbackQuery"
    )

    assert captured[
        "data"
    ] == {
        "callback_query_id":
            "callback-1",
        "text":
            "Done",
    }
