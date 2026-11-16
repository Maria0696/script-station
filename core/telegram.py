from core.config import HEIMDALL_BOT_TOKEN, HUGINN_BOT_TOKEN
from core.http import create_session, raise_for_status

# Reintenta límites de uso (429) y fallos de pasarela (502-504), en los que
# Telegram no llegó a procesar el mensaje. Un 500 no se repite: el mensaje
# podría haberse enviado ya y se duplicaría
session = create_session(methods={"POST"}, statuses=(429, 502, 503, 504))


def telegram_api(bot_token, method, data):
    response = session.post(
        f"https://api.telegram.org/bot{bot_token}/{method}", json=data, timeout=30
    )

    raise_for_status(response, "Telegram", method)

    return response.json()


def get_update_chat_id(update):
    # Un update es un mensaje o un botón pulsado (callback_query), que
    # trae dentro el mensaje donde estaba el botón
    message = update.get("message")

    if not isinstance(message, dict):
        callback = update.get("callback_query")
        message = callback.get("message") if isinstance(callback, dict) else None

    if not isinstance(message, dict):
        return None

    chat_id = message.get("chat", {}).get("id")

    return str(chat_id) if chat_id is not None else None


def send_message(bot_token, chat_id, text, reply_markup=None, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}

    if reply_markup:
        data["reply_markup"] = reply_markup

    if parse_mode:
        data["parse_mode"] = parse_mode

    return telegram_api(bot_token, "sendMessage", data)


def send_huginn_message(chat_id, text, reply_markup=None, parse_mode=None):
    return send_message(HUGINN_BOT_TOKEN, chat_id, text, reply_markup, parse_mode)


def send_heimdall_message(chat_id, text, reply_markup=None, parse_mode=None):
    return send_message(HEIMDALL_BOT_TOKEN, chat_id, text, reply_markup, parse_mode)


def answer_heimdall_callback(callback_query_id, text=None):
    # Telegram deja el botón "cargando" hasta que se responde el callback
    data = {"callback_query_id": callback_query_id}

    if text:
        data["text"] = text

    return telegram_api(HEIMDALL_BOT_TOKEN, "answerCallbackQuery", data)


def answer_huginn_callback(callback_query_id):
    return telegram_api(
        HUGINN_BOT_TOKEN,
        "answerCallbackQuery",
        {"callback_query_id": callback_query_id},
    )
