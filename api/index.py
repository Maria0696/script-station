import base64
import json
import os
from urllib import parse, request
from fastapi import FastAPI, Request


app = FastAPI()


# Variables de entorno de Vercel
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])

IGDB_CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
IGDB_CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


# Repositorio donde guardamos la watchlist
GITHUB_REPO = "Maria0696/script-station"
GITHUB_BRANCH = "master"
WATCHLIST_PATH = "data/watchlist.json"


def telegram_api(method, data):
    # Ejecuta una llamada a la API de Telegram
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/{method}"
    )

    body = json.dumps(data).encode("utf-8")

    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


def send_telegram_message(
    chat_id,
    text,
    reply_markup=None,
):
    # Envía un mensaje al chat
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return telegram_api(
        "sendMessage",
        data,
    )


def answer_callback_query(callback_query_id):
    # Cierra la animación del botón pulsado
    telegram_api(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_query_id
        },
    )


def get_igdb_token():
    # Obtiene un token temporal para IGDB
    params = parse.urlencode(
        {
            "client_id": IGDB_CLIENT_ID,
            "client_secret": IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }
    )

    url = (
        "https://id.twitch.tv/oauth2/token?"
        + params
    )

    req = request.Request(
        url,
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(
            response.read()
        )["access_token"]


def search_igdb_games(game_name):
    # Busca juegos por nombre en IGDB
    token = get_igdb_token()

    safe_name = (
        game_name
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    query = f"""
    search "{safe_name}";
    fields
        id,
        name,
        first_release_date;
    limit 5;
    """

    req = request.Request(
        "https://api.igdb.com/v4/games",
        data=query.encode("utf-8"),
        headers={
            "Client-ID": IGDB_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


def get_igdb_game(game_id):
    # Busca un juego exacto por ID
    token = get_igdb_token()

    query = f"""
    fields id,name;
    where id = {game_id};
    limit 1;
    """

    req = request.Request(
        "https://api.igdb.com/v4/games",
        data=query.encode("utf-8"),
        headers={
            "Client-ID": IGDB_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        games = json.loads(response.read())

    if not games:
        return None

    return games[0]


def github_request(
    method,
    path,
    data=None,
):
    # Ejecuta una llamada a la API de GitHub
    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPO}/{path}"
    )

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method=method,
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


def get_watchlist():
    # Lee watchlist.json desde GitHub
    result = github_request(
        "GET",
        (
            f"contents/{WATCHLIST_PATH}"
            f"?ref={GITHUB_BRANCH}"
        ),
    )

    content = base64.b64decode(
        result["content"]
    ).decode("utf-8")

    return json.loads(content), result["sha"]


def save_watchlist(watchlist, sha):
    # Actualiza watchlist.json en GitHub
    content = json.dumps(
        watchlist,
        ensure_ascii=False,
        indent=2,
    )

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    github_request(
        "PUT",
        f"contents/{WATCHLIST_PATH}",
        {
            "message": "chore: update game watchlist",
            "content": encoded_content,
            "sha": sha,
            "branch": GITHUB_BRANCH,
        },
    )


def build_watchlist_message():
    # Construye el mensaje de /watchlist
    watchlist, _ = get_watchlist()

    if not watchlist:
        return "👀 Tu watchlist está vacía."

    lines = [
        "👀 MY WATCHLIST",
        "",
    ]

    for game in watchlist:
        lines.append(
            f"• {game['name']}"
        )

    return "\n".join(lines)


def build_search_keyboard(games):
    # Crea un botón por resultado de IGDB
    buttons = []

    for game in games:
        buttons.append(
            [
                {
                    "text": game["name"],
                    "callback_data": (
                        f"watch:{game['id']}"
                    ),
                }
            ]
        )

    return {
        "inline_keyboard": buttons
    }


def build_unwatch_keyboard(watchlist):
    # Crea un botón por juego guardado
    buttons = []

    for game in watchlist:
        buttons.append(
            [
                {
                    "text": f"❌ {game['name']}",
                    "callback_data": (
                        f"unwatch:{game['id']}"
                    ),
                }
            ]
        )

    return {
        "inline_keyboard": buttons
    }


def add_game_to_watchlist(game_id):
    # Añade un juego a la watchlist
    game = get_igdb_game(game_id)

    if not game:
        return None, False

    watchlist, sha = get_watchlist()

    # Evita duplicados
    already_exists = any(
        item["id"] == game["id"]
        for item in watchlist
    )

    if already_exists:
        return game, False

    watchlist.append(
        {
            "id": game["id"],
            "name": game["name"],
        }
    )

    save_watchlist(
        watchlist,
        sha,
    )

    return game, True


def remove_game_from_watchlist(game_id):
    # Elimina un juego de la watchlist
    watchlist, sha = get_watchlist()

    game = next(
        (
            item
            for item in watchlist
            if item["id"] == game_id
        ),
        None,
    )

    if not game:
        return None, False

    updated_watchlist = [
        item
        for item in watchlist
        if item["id"] != game_id
    ]

    save_watchlist(
        updated_watchlist,
        sha,
    )

    return game, True


# Para comprobar el endpoint:
# https://script-station.vercel.app/api/telegram
@app.get("/api/telegram")
@app.get("/api/index")
def health_check():
    return {
        "ok": True,
        "message": "Telegram endpoint is running",
    }


@app.post("/api/telegram")
@app.post("/api/index")
async def telegram_webhook(request_data: Request):
    # Recibe el update enviado por Telegram
    update = await request_data.json()

    # Pulsación de un botón
    callback = update.get("callback_query")

    if isinstance(callback, dict):
        callback_id = callback.get("id")
        callback_data = callback.get("data", "")

        message = callback.get(
            "message",
            {},
        )

        chat_id = str(
            message
            .get("chat", {})
            .get("id", "")
        )

        # Ignora usuarios no autorizados
        if chat_id != ALLOWED_CHAT_ID:
            return {"ok": True}

        if callback_id:
            answer_callback_query(
                callback_id
            )

        # Añadir juego seleccionado
        if callback_data.startswith("watch:"):
            game_id = int(
                callback_data.split(":")[1]
            )

            game, added = (
                add_game_to_watchlist(
                    game_id
                )
            )

            if not game:
                send_telegram_message(
                    chat_id,
                    "❌ No he podido encontrar el juego.",
                )

            elif added:
                send_telegram_message(
                    chat_id,
                    (
                        "✅ Añadido a tu watchlist\n\n"
                        f"🎮 {game['name']}"
                    ),
                )

            else:
                send_telegram_message(
                    chat_id,
                    (
                        "ℹ️ Ese juego ya está "
                        "en tu watchlist."
                    ),
                )

        # Eliminar juego seleccionado
        elif callback_data.startswith("unwatch:"):
            game_id = int(
                callback_data.split(":")[1]
            )

            game, removed = (
                remove_game_from_watchlist(
                    game_id
                )
            )

            if not removed:
                send_telegram_message(
                    chat_id,
                    (
                        "ℹ️ Ese juego ya no está "
                        "en tu watchlist."
                    ),
                )

            else:
                send_telegram_message(
                    chat_id,
                    (
                        "🗑️ Eliminado de tu watchlist\n\n"
                        f"🎮 {game['name']}"
                    ),
                )

        return {"ok": True}

    # Mensaje normal
    message = update.get("message")

    if not isinstance(message, dict):
        return {"ok": True}

    chat_id = str(
        message
        .get("chat", {})
        .get("id", "")
    )

    text = message.get(
        "text",
        "",
    ).strip()

    # Solo acepta nuestro chat
    if chat_id != ALLOWED_CHAT_ID:
        return {"ok": True}

    # Mostrar watchlist
    if text == "/watchlist":
        send_telegram_message(
            chat_id,
            build_watchlist_message(),
        )

    # Mostrar juegos disponibles para eliminar
    elif text == "/unwatch":
        watchlist, _ = get_watchlist()

        if not watchlist:
            send_telegram_message(
                chat_id,
                "👀 Tu watchlist está vacía.",
            )

        else:
            send_telegram_message(
                chat_id,
                "🗑️ ¿Qué juego quieres eliminar?",
                build_unwatch_keyboard(
                    watchlist
                ),
            )

    # Buscar juego para añadir
    elif text.startswith("/watch "):
        search_term = (
            text[len("/watch "):]
            .strip()
        )

        if not search_term:
            send_telegram_message(
                chat_id,
                "Uso: /watch nombre del juego",
            )

            return {"ok": True}

        games = search_igdb_games(
            search_term
        )

        if not games:
            send_telegram_message(
                chat_id,
                (
                    "❌ No he encontrado "
                    "ningún juego."
                ),
            )

        else:
            send_telegram_message(
                chat_id,
                "🔎 ¿Qué juego quieres añadir?",
                build_search_keyboard(games),
            )

    # Ayuda si falta el nombre
    elif text == "/watch":
        send_telegram_message(
            chat_id,
            "Uso: /watch nombre del juego",
        )

    return {"ok": True}
