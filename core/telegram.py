import json
import os
from urllib import request

HUGINN_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

HEIMDALL_BOT_TOKEN = os.getenv(
    "TELEGRAM_HEIMDALL_BOT_TOKEN"
)


def telegram_api(
    bot_token,
    method,
    data,
):
    # Ejecuta una llamada a Telegram
    url = (
        "https://api.telegram.org/"
        f"bot{bot_token}/{method}"
    )

    body = json.dumps(
        data
    ).encode(
        "utf-8"
    )

    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type":
                "application/json",
        },
        method="POST",
    )

    with request.urlopen(
        req,
        timeout=30,
    ) as response:
        return json.loads(
            response.read()
        )


def send_message(
    bot_token,
    chat_id,
    text,
    reply_markup=None,
    parse_mode=None,
):
    # Envía un mensaje genérico a Telegram
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data[
            "reply_markup"
        ] = reply_markup

    if parse_mode:
        data[
            "parse_mode"
        ] = parse_mode

    return telegram_api(
        bot_token,
        "sendMessage",
        data,
    )


def send_huginn_message(
    chat_id,
    text,
    reply_markup=None,
    parse_mode=None,
):
    # Envía un mensaje desde Huginn
    return send_message(
        HUGINN_BOT_TOKEN,
        chat_id,
        text,
        reply_markup,
        parse_mode,
    )


def send_heimdall_message(
    chat_id,
    text,
    reply_markup=None,
    parse_mode=None,
):
    # Envía un mensaje desde Heimdall
    return send_message(
        HEIMDALL_BOT_TOKEN,
        chat_id,
        text,
        reply_markup,
        parse_mode,
    )


def answer_heimdall_callback(
    callback_query_id,
    text=None,
):
    # Cierra la animación del botón pulsado
    data = {
        "callback_query_id":
            callback_query_id,
    }

    if text:
        data[
            "text"
        ] = text

    return telegram_api(
        HEIMDALL_BOT_TOKEN,
        "answerCallbackQuery",
        data,
    )


def answer_huginn_callback(
    callback_query_id,
):
    # Cierra la animación del botón pulsado
    return telegram_api(
        HUGINN_BOT_TOKEN,
        "answerCallbackQuery",
        {
            "callback_query_id":
                callback_query_id,
        },
    )
