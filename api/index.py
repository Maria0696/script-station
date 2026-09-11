import base64
import json
import os
from datetime import datetime, timezone
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


# IDs de plataformas de IGDB
PLATFORM_LABELS = {
    167: "PS5",
    508: "Switch 2",
    6: "PC",
    169: "Xbox Series",
    48: "PS4",
    49: "Xbox One",
    130: "Switch",
    390: "PS VR2",
    471: "Meta Quest",  # Meta Quest 3
    386: "Meta Quest",  # Meta Quest 2
    163: "SteamVR",
}


# Orden visual de las plataformas
PLATFORM_ORDER = [
    167,
    508,
    6,
    169,
    48,
    49,
    130,
    390,
    471,
    386,
    163,
]


# Regiones válidas para fechas de lanzamiento
VALID_REGIONS = {
    "europe",
    "worldwide",
}


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


def igdb_request(token, endpoint, query):
    # Ejecuta una consulta a IGDB
    req = request.Request(
        f"https://api.igdb.com/v4/{endpoint}",
        data=query.encode("utf-8"),
        headers={
            "Client-ID": IGDB_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


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

    return igdb_request(
        token,
        "games",
        query,
    )


def get_igdb_game(game_id):
    # Busca un juego exacto
    token = get_igdb_token()

    query = f"""
    fields
        id,
        name,
        first_release_date,
        platforms;
    where id = {game_id};
    limit 1;
    """

    games = igdb_request(
        token,
        "games",
        query,
    )

    if not games:
        return None

    return games[0]


def get_platform_release_dates(game_id):
    # Obtiene fechas de lanzamiento por plataforma
    token = get_igdb_token()

    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    query = f"""
    fields
        platform,
        date,
        release_region.region;

    where game = {game_id}
        & platform = ({platform_ids});

    limit 500;
    sort date asc;
    """

    releases = igdb_request(
        token,
        "release_dates",
        query,
    )

    release_dates = {}

    for release in releases:
        platform_id = release.get("platform")
        timestamp = release.get("date")
        region = release.get("release_region")

        if platform_id not in PLATFORM_LABELS:
            continue

        # Si hay región, solo usamos Europa o Worldwide
        if isinstance(region, dict):
            region_name = region.get(
                "region",
                "",
            ).lower()

            if (
                region_name
                and region_name not in VALID_REGIONS
            ):
                continue

        release_date = format_release_date(
            timestamp
        )

        if not release_date:
            continue

        # Conserva la primera fecha válida
        if platform_id not in release_dates:
            release_dates[platform_id] = release_date

    return release_dates


def format_release_date(timestamp):
    # Convierte timestamp IGDB a YYYY-MM-DD
    if not timestamp:
        return None

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).date().isoformat()


def display_release_date(date_string):
    # Convierte YYYY-MM-DD a DD-MM-YYYY
    if not date_string:
        return "Sin fecha"

    return datetime.strptime(
        date_string,
        "%Y-%m-%d",
    ).strftime("%d-%m-%Y")


def build_platform_data(game):
    # Une plataformas y sus fechas
    release_dates = get_platform_release_dates(
        game["id"]
    )

    platform_ids = set(
        game.get(
            "platforms",
            [],
        )
    )

    # Incluye plataformas presentes en release_dates
    platform_ids.update(
        release_dates.keys()
    )

    platforms = []
    labels_added = set()

    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[platform_id]

        # Agrupa Meta Quest 2 y 3 visualmente
        if label in labels_added:
            continue

        platforms.append(
            {
                "id": platform_id,
                "label": label,
                "release_date": release_dates.get(
                    platform_id
                ),
            }
        )

        labels_added.add(label)

    return platforms


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


def build_help_message():
    # Lista de comandos disponibles
    return (
        "🤖 COMANDOS DISPONIBLES\n\n"
        "/watch nombre\n"
        "Añade un juego a tu watchlist.\n\n"
        "/watchlist\n"
        "Muestra los juegos guardados.\n\n"
        "/unwatch\n"
        "Elimina un juego de tu watchlist.\n\n"
        "/help\n"
        "Muestra esta ayuda."
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
            f"🎮 {game['name']}"
        )

        platforms = game.get(
            "platforms",
            [],
        )

        # Nuevo formato con fecha por plataforma
        if (
            platforms
            and isinstance(platforms[0], dict)
        ):
            for platform in platforms:
                lines.append(
                    f"      {platform['label']} — "
                    f"{display_release_date(platform.get('release_date'))}"
                )

        # Compatibilidad con formato anterior
        elif platforms:
            release_date = display_release_date(
                game.get("release_date")
            )

            lines.append(
                f"      {' | '.join(platforms)} — "
                f"{release_date}"
            )

        else:
            lines.append(
                "      Plataformas por confirmar — "
                f"{display_release_date(game.get('release_date'))}"
            )

        lines.append("")

    return "\n".join(lines).rstrip()


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
    # Añade juego con fechas por plataforma
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

    release_date = format_release_date(
        game.get("first_release_date")
    )

    platforms = build_platform_data(
        game
    )

    watchlist.append(
        {
            "id": game["id"],
            "name": game["name"],
            "release_date": release_date,
            "platforms": platforms,
        }
    )

    save_watchlist(
        watchlist,
        sha,
    )

    # Datos usados para responder en Telegram
    game["release_date"] = release_date
    game["platform_data"] = platforms

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
                lines = [
                    "✅ Añadido a tu watchlist",
                    "",
                    f"🎮 {game['name']}",
                ]

                platforms = game.get(
                    "platform_data",
                    [],
                )

                if platforms:
                    for platform in platforms:
                        lines.append(
                            f"      {platform['label']} — "
                            f"{display_release_date(platform.get('release_date'))}"
                        )

                else:
                    lines.append(
                        "      Plataformas por confirmar — "
                        f"{display_release_date(game.get('release_date'))}"
                    )

                send_telegram_message(
                    chat_id,
                    "\n".join(lines),
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

    # Mostrar ayuda
    if text == "/help":
        send_telegram_message(
            chat_id,
            build_help_message(),
        )

    # Mostrar watchlist
    elif text == "/watchlist":
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

        games = search_igdb_games(
            search_term
        )

        if not games:
            send_telegram_message(
                chat_id,
                "❌ No he encontrado ningún juego.",
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
