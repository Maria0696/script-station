import os

from core.telegram import (
    send_message,
)

CHANNELS = {
    "huginn": {
        "bot_token":
            "TELEGRAM_BOT_TOKEN",
        "chat_id":
            "TELEGRAM_CHAT_ID",
    },
    "heimdall": {
        "bot_token":
            "TELEGRAM_HEIMDALL_BOT_TOKEN",
        "chat_id":
            "TELEGRAM_HEIMDALL_CHAT_ID",
    },
}


EVENT_ROUTES = {
    "workflow.failed":
        "heimdall",
    "game.release_changed":
        "huginn",
}


class NotificationService:

    def _get_channel_config(
        self,
        channel,
    ):
        # Obtiene credenciales del canal
        config = CHANNELS.get(
            channel
        )

        if not config:
            raise ValueError(
                "Unknown notification "
                f"channel: {channel}"
            )

        bot_token = os.environ[
            config["bot_token"]
        ]

        chat_id = str(
            os.environ[
                config["chat_id"]
            ]
        )

        return (
            bot_token,
            chat_id,
        )

    def _get_event_channel(
        self,
        event,
    ):
        # Obtiene el canal asociado al evento
        channel = EVENT_ROUTES.get(
            event
        )

        if not channel:
            raise ValueError(
                "Unknown notification "
                f"event: {event}"
            )

        return channel

    def emit(
        self,
        event,
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        # Publica un evento en su canal configurado
        channel = (
            self._get_event_channel(
                event
            )
        )

        handler = getattr(
            self,
            channel,
        )

        return handler(
            text,
            reply_markup,
            parse_mode,
            chat_id,
        )

    def send(
        self,
        channel,
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        # Envía una notificación
        (
            bot_token,
            default_chat_id,
        ) = self._get_channel_config(
            channel
        )

        target_chat_id = (
            str(chat_id)
            if chat_id is not None
            else default_chat_id
        )

        return send_message(
            bot_token,
            target_chat_id,
            text,
            reply_markup,
            parse_mode,
        )

    def huginn(
        self,
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        # Envía una notificación por Huginn
        return self.send(
            "huginn",
            text,
            reply_markup,
            parse_mode,
            chat_id,
        )

    def heimdall(
        self,
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        # Envía una notificación por Heimdall
        return self.send(
            "heimdall",
            text,
            reply_markup,
            parse_mode,
            chat_id,
        )


notifications = NotificationService()