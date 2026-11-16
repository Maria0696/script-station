import json

import pytest
import requests

from core import telegram


class FakeResponse:
    # Respuesta mínima de requests

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = json.dumps(data)

    def json(self):
        return self.data


def test_telegram_api(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)

        return FakeResponse({"ok": True})

    monkeypatch.setattr(telegram.session, "post", fake_post)

    result = telegram.telegram_api(
        "test-token", "sendMessage", {"chat_id": "123", "text": "Hello"}
    )

    assert result == {"ok": True}

    assert captured == {
        "url": "https://api.telegram.org/bottest-token/sendMessage",
        "json": {"chat_id": "123", "text": "Hello"},
        "timeout": 30,
    }


def test_telegram_api_error_hides_bot_token(monkeypatch):
    monkeypatch.setattr(
        telegram.session,
        "post",
        lambda url, json, timeout: FakeResponse(
            {"ok": False, "description": "Bad Request: chat not found"}, status_code=400
        ),
    )

    with pytest.raises(requests.HTTPError) as error:
        telegram.telegram_api("secret-bot-token", "sendMessage", {})

    assert "Telegram sendMessage failed: HTTP 400" in str(error.value)
    assert "chat not found" in str(error.value)
    assert "secret-bot-token" not in str(error.value)


def test_session_does_not_retry_server_errors():
    retry = telegram.session.get_adapter("https://api.telegram.org").max_retries

    assert set(retry.status_forcelist) == {429, 502, 503, 504}
    assert set(retry.allowed_methods) == {"POST"}


def test_send_message_with_parse_mode(monkeypatch):
    captured = {}

    def fake_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_api)

    keyboard = {"inline_keyboard": []}

    result = telegram.send_message(
        "token", "123", "<b>Hello</b>", reply_markup=keyboard, parse_mode="HTML"
    )

    assert result == {"ok": True}

    assert captured["data"] == {
        "chat_id": "123",
        "text": "<b>Hello</b>",
        "reply_markup": keyboard,
        "parse_mode": "HTML",
    }


def test_send_huginn_message_without_markup(monkeypatch):
    captured = {}

    def fake_telegram_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_telegram_api)

    result = telegram.send_huginn_message("123", "Hello Huginn")

    assert result == {"ok": True}

    assert captured["bot_token"] == telegram.HUGINN_BOT_TOKEN

    assert captured["method"] == "sendMessage"

    assert captured["data"] == {"chat_id": "123", "text": "Hello Huginn"}


def test_send_huginn_message_with_markup(monkeypatch):
    captured = {}

    keyboard = {
        "inline_keyboard": [[{"text": "Test Game", "callback_data": "watch:123"}]]
    }

    def fake_telegram_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_telegram_api)

    result = telegram.send_huginn_message("123", "Choose a game", keyboard)

    assert result == {"ok": True}

    assert captured["data"] == {
        "chat_id": "123",
        "text": "Choose a game",
        "reply_markup": keyboard,
    }


def test_send_heimdall_message(monkeypatch):
    captured = {}

    def fake_telegram_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_telegram_api)

    result = telegram.send_heimdall_message("456", "Workflow failed")

    assert result == {"ok": True}

    assert captured["bot_token"] == (telegram.HEIMDALL_BOT_TOKEN)

    assert captured["method"] == "sendMessage"

    assert captured["data"] == {"chat_id": "456", "text": "Workflow failed"}


def test_answer_huginn_callback(monkeypatch):
    captured = {}

    def fake_telegram_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_telegram_api)

    result = telegram.answer_huginn_callback("callback-123")

    assert result == {"ok": True}

    assert captured["bot_token"] == telegram.HUGINN_BOT_TOKEN

    assert captured["method"] == "answerCallbackQuery"

    assert captured["data"] == {"callback_query_id": "callback-123"}


def test_answer_heimdall_callback(monkeypatch):
    captured = {}

    def fake_telegram_api(bot_token, method, data):
        captured["bot_token"] = bot_token

        captured["method"] = method

        captured["data"] = data

        return {"ok": True}

    monkeypatch.setattr(telegram, "telegram_api", fake_telegram_api)

    result = telegram.answer_heimdall_callback("callback-1", "Done")

    assert result == {"ok": True}

    assert captured["bot_token"] == (telegram.HEIMDALL_BOT_TOKEN)

    assert captured["method"] == "answerCallbackQuery"

    assert captured["data"] == {"callback_query_id": "callback-1", "text": "Done"}


@pytest.mark.parametrize(
    ("update", "expected"),
    [
        ({"message": {"chat": {"id": 123}}}, "123"),
        ({"callback_query": {"message": {"chat": {"id": 456}}}}, "456"),
        ({"callback_query": {"id": "1"}}, None),
        ({"message": {"text": "/help"}}, None),
        ({"edited_message": {"chat": {"id": 123}}}, None),
    ],
)
def test_get_update_chat_id(update, expected):
    assert telegram.get_update_chat_id(update) == expected
