import pytest

from core import notifications

# ============================================================
# HUGINN
# ============================================================

def test_huginn_notification(
    monkeypatch,
):
    # Envía una notificación por Huginn
    captured = {}

    def fake_send_message(
        bot_token,
        chat_id,
        text,
        reply_markup=None,
        parse_mode=None,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "chat_id"
        ] = chat_id

        captured[
            "text"
        ] = text

        captured[
            "reply_markup"
        ] = reply_markup

        captured[
            "parse_mode"
        ] = parse_mode

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        notifications,
        "send_message",
        fake_send_message,
    )

    service = (
        notifications
        .NotificationService()
    )

    result = service.huginn(
        "Hello Huginn",
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured["bot_token"]
        == "test-huginn-token"
    )

    assert (
        captured["chat_id"]
        == "123456"
    )

    assert (
        captured["text"]
        == "Hello Huginn"
    )

    assert (
        captured["reply_markup"]
        is None
    )

    assert (
        captured["parse_mode"]
        is None
    )


def test_huginn_notification_with_parse_mode(
    monkeypatch,
):
    # Envía HTML mediante Huginn
    captured = {}

    def fake_send_message(
        bot_token,
        chat_id,
        text,
        reply_markup=None,
        parse_mode=None,
    ):
        captured[
            "parse_mode"
        ] = parse_mode

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        notifications,
        "send_message",
        fake_send_message,
    )

    service = (
        notifications
        .NotificationService()
    )

    service.huginn(
        "<b>Test</b>",
        parse_mode="HTML",
    )

    assert (
        captured["parse_mode"]
        == "HTML"
    )


# ============================================================
# HEIMDALL
# ============================================================

def test_heimdall_notification(
    monkeypatch,
):
    # Envía una notificación por Heimdall
    captured = {}

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "🔄 Re-run",
                    "callback_data":
                        "rerun:123",
                }
            ]
        ]
    }

    def fake_send_message(
        bot_token,
        chat_id,
        text,
        reply_markup=None,
        parse_mode=None,
    ):
        captured[
            "bot_token"
        ] = bot_token

        captured[
            "chat_id"
        ] = chat_id

        captured[
            "text"
        ] = text

        captured[
            "reply_markup"
        ] = reply_markup

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        notifications,
        "send_message",
        fake_send_message,
    )

    service = (
        notifications
        .NotificationService()
    )

    result = service.heimdall(
        "Workflow failed",
        reply_markup=keyboard,
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured["bot_token"]
        == "test-heimdall-token"
    )

    assert (
        captured["chat_id"]
        == "654321"
    )

    assert (
        captured["text"]
        == "Workflow failed"
    )

    assert (
        captured["reply_markup"]
        == keyboard
    )


def test_notification_custom_chat_id(
    monkeypatch,
):
    # Permite sobrescribir el chat destino
    captured = {}

    def fake_send_message(
        bot_token,
        chat_id,
        text,
        reply_markup=None,
        parse_mode=None,
    ):
        captured[
            "chat_id"
        ] = chat_id

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        notifications,
        "send_message",
        fake_send_message,
    )

    service = (
        notifications
        .NotificationService()
    )

    service.heimdall(
        "Test",
        chat_id="999999",
    )

    assert (
        captured["chat_id"]
        == "999999"
    )


# ============================================================
# ERRORES
# ============================================================

def test_unknown_notification_channel():
    # Rechaza canales desconocidos
    service = (
        notifications
        .NotificationService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Unknown notification "
            "channel"
        ),
    ):
        service.send(
            "odin",
            "Test",
        )
