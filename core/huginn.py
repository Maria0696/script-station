# Huginn: bot de Telegram para seguir lanzamientos de videojuegos.
# api/index.py le pasa cada update a handle_huginn_update. Es un bot de un
# solo usuario: todo lo que no venga de HUGINN_CHAT_ID se ignora.
# Los avisos automáticos (retrasos, salidas) no salen de aquí sino del
# monitor diario, scripts/watchlist_monitor.py.

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.config import HUGINN_CHAT_ID, RELEASED_STATUS
from core.github import get_watchlist, update_watchlist
from core.igdb import (
    build_platform_data,
    display_platform_date,
    display_release_date,
    format_release_date,
    get_igdb_game,
    get_platform_names,
    get_release_year,
    search_igdb_games,
)
from core.telegram import (
    answer_huginn_callback,
    get_update_chat_id,
    send_huginn_message,
)

logger = logging.getLogger(__name__)

MADRID_TIMEZONE = ZoneInfo("Europe/Madrid")

NEXT_GAME_LIMIT = 5

ERROR_MESSAGE = "❌ No he podido completar la acción. Inténtalo de nuevo en un rato."


def build_title(title, icon="", indent=0):
    title_text = f"{icon} {title}" if icon else title

    return f"━━━━━━━━━━━━━━━━━━━\n{' ' * indent}{title_text}\n━━━━━━━━━━━━━━━━━━━\n\n"


# ============================================================
# MENSAJES
# ============================================================


def build_help_message():
    return (
        build_title("COMANDOS", icon="🤖", indent=22)
        + "/watch nombre\n"
        + "Añade un juego a tu lista.\n\n"
        + "/watchlist\n"
        + "Muestra los juegos guardados.\n\n"
        + "/next\n"
        + "Muestra los próximos lanzamientos.\n\n"
        + "/released\n"
        + "Muestra los juegos de tu lista que ya han salido.\n\n"
        + "/unwatch\n"
        + "Elimina un juego de tu lista.\n\n"
        + "/help\n"
        + "Muestra esta ayuda."
    )


def build_watch_search_message():
    return (
        "¿Qué juego quieres añadir?\n\n"
        "Si no aparece, escribe el nombre completo: "
        "/watch tomb raider legacy of atlantis"
    )


def build_watch_added_message(game):
    return f"✅ Añadido: {game['name']}"


def build_already_added_message(game):
    return f"ℹ️ Ese juego ya estaba en tu lista: {game['name']}"


def build_unwatch_message():
    return "¿Qué juego quieres eliminar?"


def build_removed_message(game):
    return f"🗑️ Eliminado: {game['name']}"


def is_archived(game):
    return game.get("status") == RELEASED_STATUS


def build_watchlist_message():
    watchlist, _ = get_watchlist()

    active_games = [game for game in watchlist if not is_archived(game)]
    archived_count = len(watchlist) - len(active_games)
    archived_line = f"📦 Ya lanzados: {archived_count} (/released)"

    if not active_games:
        if archived_count:
            return f"👀 No tienes juegos pendientes de salir.\n\n{archived_line}"

        return "👀 Tu lista está vacía."

    lines = [build_title("MI LISTADO DE JUEGOS", icon="👀", indent=12).rstrip(), ""]

    for game in active_games:
        lines.append(f"🎮 {game['name']}")

        platforms = game.get("platforms", [])

        if platforms and isinstance(platforms[0], dict):
            for platform in platforms:
                lines.append(
                    f"      {platform['label']} — {display_platform_date(platform)}"
                )

        # Formato antiguo: platforms era una lista de etiquetas con una única
        # fecha por juego. El monitor lo migra en su siguiente ejecución
        elif platforms:
            release_date = display_release_date(game.get("release_date"))

            lines.append(f"      {' | '.join(platforms)} — {release_date}")

        else:
            release_date = display_release_date(game.get("release_date"))

            lines.append(f"      Plataformas por confirmar — {release_date}")

        lines.append("")

    if archived_count:
        lines.append(archived_line)

    return "\n".join(lines).rstrip()


def build_released_message():
    watchlist, _ = get_watchlist()

    released_games = sorted(
        (game for game in watchlist if is_archived(game)),
        key=lambda game: game.get("released_on") or "",
        reverse=True,
    )

    if not released_games:
        return "📦 Todavía no ha salido ningún juego de tu lista."

    lines = [build_title("YA LANZADOS", icon="📦", indent=18).rstrip(), ""]

    for game in released_games:
        lines.append(f"🎮 {game['name']}")
        lines.append(f"      {display_release_date(game.get('released_on'))}")
        lines.append("")

    return "\n".join(lines).rstrip()


# ============================================================
# NEXT
# ============================================================


def parse_release_date(date_string):
    if not date_string:
        return None

    try:
        return date.fromisoformat(date_string)

    except ValueError:
        return None


def get_upcoming_games():
    watchlist, _ = get_watchlist()

    today = datetime.now(MADRID_TIMEZONE).date()

    upcoming_games = []

    for game in watchlist:
        if is_archived(game):
            continue

        platforms = game.get("platforms", [])

        future_releases = []

        if platforms and isinstance(platforms[0], dict):
            for platform in platforms:
                date_string = platform.get("release_date")

                release_date = parse_release_date(date_string)

                if not release_date or release_date < today:
                    continue

                future_releases.append(
                    {
                        "label": platform["label"],
                        "date": date_string,
                        "date_obj": release_date,
                        "display": display_platform_date(platform),
                    }
                )

        # Formato antiguo (ver build_watchlist_message)
        else:
            date_string = game.get("release_date")

            release_date = parse_release_date(date_string)

            if release_date and release_date >= today:
                if platforms:
                    label = " | ".join(platforms)
                else:
                    label = "Plataformas por confirmar"

                future_releases.append(
                    {
                        "label": label,
                        "date": date_string,
                        "date_obj": release_date,
                        "display": display_release_date(date_string),
                    }
                )

        if not future_releases:
            continue

        future_releases.sort(key=lambda release: release["date_obj"])

        upcoming_games.append(
            {
                "name": game["name"],
                "next_date": future_releases[0]["date_obj"],
                "releases": future_releases,
            }
        )

    upcoming_games.sort(key=lambda game: (game["next_date"], game["name"].lower()))

    return upcoming_games[:NEXT_GAME_LIMIT]


def build_next_message():
    upcoming_games = get_upcoming_games()

    if not upcoming_games:
        return "⏭️ No tienes próximos lanzamientos con fecha."

    lines = [build_title("PRÓXIMOS LANZAMIENTOS", icon="⏭️", indent=10).rstrip(), ""]

    for game in upcoming_games:
        lines.append(f"🎮 {game['name']}")

        for release in game["releases"]:
            lines.append(f"      {release['label']} — {release['display']}")

        lines.append("")

    return "\n".join(lines).rstrip()


# ============================================================
# BOTONES
# ============================================================


def build_search_keyboard(games):
    # callback_data admite 64 bytes: solo viaja el id del juego
    buttons = []

    for game in games:
        buttons.append(
            [
                {
                    "text": build_search_button_text(game),
                    "callback_data": f"watch:{game['id']}",
                }
            ]
        )

    return {"inline_keyboard": buttons}


def build_search_button_text(game):
    # "Tomb Raider (1996)" y "Tomb Raider (2013) · PS4, PC" se distinguen;
    # solo con el nombre no
    text = f"{game['name']} ({get_release_year(game)})"

    platforms = get_platform_names(game.get("platforms", []))

    return f"{text} · {platforms}" if platforms else text


def build_unwatch_keyboard(watchlist):
    buttons = []

    for game in watchlist:
        buttons.append(
            [{"text": f"❌ {game['name']}", "callback_data": f"unwatch:{game['id']}"}]
        )

    return {"inline_keyboard": buttons}


# ============================================================
# WATCHLIST
# ============================================================


def add_game_to_watchlist(game_id):
    game = get_igdb_game(game_id)

    if not game:
        return None, False

    def add(watchlist):
        existing_game = next(
            (item for item in watchlist if item["id"] == game["id"]), None
        )

        if existing_game:
            return (existing_game, False), False

        release_date = format_release_date(game.get("first_release_date"))

        platforms = build_platform_data(game)

        watchlist.append(
            {
                "id": game["id"],
                "name": game["name"],
                "release_date": release_date,
                "platforms": platforms,
            }
        )

        # Para el mensaje de confirmación
        game["release_date"] = release_date
        game["platform_data"] = platforms

        return (game, True), True

    # add() se repite sobre la versión nueva si el monitor guardó a la vez
    return update_watchlist(add)


def remove_game_from_watchlist(game_id):
    def remove(watchlist):
        game = next((item for item in watchlist if item["id"] == game_id), None)

        if not game:
            return (None, False), False

        watchlist[:] = [item for item in watchlist if item["id"] != game_id]

        return (game, True), True

    return update_watchlist(remove)


# ============================================================
# CALLBACKS
# ============================================================


def handle_watch_callback(chat_id, game_id):
    game, added = add_game_to_watchlist(game_id)

    if not game:
        send_huginn_message(chat_id, ("❌ No he podido encontrar el juego."))

        return

    if not added:
        send_huginn_message(chat_id, build_already_added_message(game))

        return

    send_huginn_message(chat_id, build_watch_added_message(game))


def handle_unwatch_callback(chat_id, game_id):
    game, removed = remove_game_from_watchlist(game_id)

    if not removed:
        send_huginn_message(chat_id, "ℹ️ Ese juego ya no está en tu lista.")

        return

    send_huginn_message(chat_id, build_removed_message(game))


def handle_huginn_callback(callback):
    callback_id = callback.get("id")

    callback_data = callback.get("data", "")

    message = callback.get("message", {})

    chat_id = str(message.get("chat", {}).get("id", ""))

    # Bot de un solo usuario: otros chats se ignoran sin responder
    if chat_id != HUGINN_CHAT_ID:
        return {"ok": True}

    if callback_id:
        answer_huginn_callback(callback_id)

    if callback_data.startswith("watch:"):
        game_id = int(callback_data.split(":", 1)[1])

        handle_watch_callback(chat_id, game_id)

    elif callback_data.startswith("unwatch:"):
        game_id = int(callback_data.split(":", 1)[1])

        handle_unwatch_callback(chat_id, game_id)

    return {"ok": True}


# ============================================================
# COMANDOS
# ============================================================


def handle_huginn_message(message):
    chat_id = str(message.get("chat", {}).get("id", ""))

    text = message.get("text", "").strip()

    if chat_id != HUGINN_CHAT_ID:
        return {"ok": True}

    if text == "/help":
        send_huginn_message(chat_id, build_help_message())

    elif text == "/next":
        send_huginn_message(chat_id, build_next_message())

    elif text == "/watchlist":
        send_huginn_message(chat_id, build_watchlist_message())

    elif text == "/released":
        send_huginn_message(chat_id, build_released_message())

    elif text == "/unwatch":
        watchlist, _ = get_watchlist()

        if not watchlist:
            send_huginn_message(chat_id, "👀 Tu lista está vacía.")

        else:
            send_huginn_message(
                chat_id, build_unwatch_message(), build_unwatch_keyboard(watchlist)
            )

    elif text.startswith("/watch "):
        search_term = text[len("/watch ") :].strip()

        if not search_term:
            send_huginn_message(chat_id, ("Uso: /watch nombre del juego"))

            return {"ok": True}

        games = search_igdb_games(search_term)

        if not games:
            send_huginn_message(chat_id, ("❌ No he encontrado ningún juego."))

        else:
            send_huginn_message(
                chat_id, build_watch_search_message(), build_search_keyboard(games)
            )

    elif text == "/watch":
        send_huginn_message(chat_id, ("Uso: /watch nombre del juego"))

    return {"ok": True}


# ============================================================
# ENTRADA
# ============================================================


def dispatch_huginn_update(update):
    callback = update.get("callback_query")

    if isinstance(callback, dict):
        return handle_huginn_callback(callback)

    message = update.get("message")

    if isinstance(message, dict):
        return handle_huginn_message(message)

    return {"ok": True}


def report_huginn_error(update):
    chat_id = get_update_chat_id(update)

    if chat_id != HUGINN_CHAT_ID:
        return

    try:
        send_huginn_message(chat_id, ERROR_MESSAGE)

    except Exception:
        logger.exception("Could not send the Huginn error message")


def handle_huginn_update(update):
    # Un fallo (IGDB o GitHub caídos) se registra y se avisa en el chat;
    # a Telegram se le responde OK para que no reenvíe el mismo update
    try:
        return dispatch_huginn_update(update)

    except Exception:
        logger.exception("Huginn could not process an update")

        report_huginn_error(update)

        return {"ok": True}
