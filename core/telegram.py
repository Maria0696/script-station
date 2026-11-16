import json
from urllib import request

from core.config import HEIMDALL_BOT_TOKEN, HUGINN_BOT_TOKEN


def telegram_api(bot_token, method, data):
    # Ejecuta una llamada a Telegram
    url = f"https://api.telegram.org/bot{bot_token}/{method}"

    body = json.dumps(data).encode("utf-8")

    req = request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )

    # La URL siempre parte de una base https:// fija
    with request.urlopen(req, timeout=30) as response:  # noqa: S310
        return json.loads(response.read())


def get_update_chat_id(update):
    # Chat de un mensaje o del mensaje de un botón pulsado
    message = update.get("message")

    if not isinstance(message, dict):
        callback = update.get("callback_query")
        message = callback.get("message") if isinstance(callback, dict) else None

    if not isinstance(message, dict):
        return None

    chat_id = message.get("chat", {}).get("id")

    return str(chat_id) if chat_id is not None else None


def send_message(bot_token, chat_id, text, reply_markup=None, parse_mode=None):
    # Envía un mensaje genérico a Telegram
    data = {"chat_id": chat_id, "text": text}

    if reply_markup:
        data["reply_markup"] = reply_markup

    if parse_mode:
        data["parse_mode"] = parse_mode

    return telegram_api(bot_token, "sendMessage", data)


def send_huginn_message(chat_id, text, reply_markup=None, parse_mode=None):
    # Envía un mensaje desde Huginn
    return send_message(HUGINN_BOT_TOKEN, chat_id, text, reply_markup, parse_mode)


def send_heimdall_message(chat_id, text, reply_markup=None, parse_mode=None):
    # Envía un mensaje desde Heimdall
    return send_message(HEIMDALL_BOT_TOKEN, chat_id, text, reply_markup, parse_mode)


def answer_heimdall_callback(callback_query_id, text=None):
    # Cierra la animación del botón pulsado
    data = {"callback_query_id": callback_query_id}

    if text:
        data["text"] = text

    return telegram_api(HEIMDALL_BOT_TOKEN, "answerCallbackQuery", data)


def answer_huginn_callback(callback_query_id):
    # Cierra la animación del botón pulsado
    return telegram_api(
        HUGINN_BOT_TOKEN,
        "answerCallbackQuery",
        {"callback_query_id": callback_query_id},
    )
