from datetime import datetime
from zoneinfo import ZoneInfo

from core.config import (
    HUGINN_CHAT_ID,
)

from core.github import (
    get_watchlist,
    save_watchlist,
)

from core.igdb import (
    build_platform_data,
    display_release_date,
    format_release_date,
    get_igdb_game,
    search_igdb_games,
)

from core.telegram import (
    answer_huginn_callback,
    send_huginn_message,
)


MADRID_TIMEZONE = ZoneInfo(
    "Europe/Madrid"
)

NEXT_GAME_LIMIT = 5


def build_title(
    title,
    icon="",
    indent=0,
):
    # Encabezado con posición configurable
    title_text = (
        f"{icon} {title}"
        if icon
        else title
    )

    return (
        "━━━━━━━━━━━━━━━━━━━\n"
        f"{' ' * indent}{title_text}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ============================================================
# MENSAJES
# ============================================================

def build_help_message():
    # Lista de comandos de Huginn
    return (
        build_title(
            "COMANDOS",
            icon="🤖",
            indent=22,
        )
        + "/watch nombre\n"
        + "Añade un juego a tu lista.\n\n"
        + "/watchlist\n"
        + "Muestra los juegos guardados.\n\n"
        + "/next\n"
        + "Muestra los próximos lanzamientos.\n\n"
        + "/unwatch\n"
        + "Elimina un juego de tu lista.\n\n"
        + "/help\n"
        + "Muestra esta ayuda."
    )


def build_watch_search_message():
    # Cabecera de resultados de búsqueda
    return (
        build_title(
            "RESULTADOS",
            icon="🔎",
            indent=22,
        )
        + "¿Qué juego quieres añadir?"
    )


def build_watch_added_message(game):
    # Confirmación al añadir un juego
    lines = [
        build_title(
            "AÑADIDO",
            icon="✅",
            indent=25,
        ).rstrip(),
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
                (
                    "      "
                    f"{platform['label']}"
                    " — "
                    f"{display_release_date(platform.get('release_date'))}"
                )
            )

    else:
        lines.append(
            (
                "      "
                "Plataformas por confirmar"
                " — "
                f"{display_release_date(game.get('release_date'))}"
            )
        )

    return "\n".join(lines)


def build_already_added_message(game):
    # Mensaje si el juego ya estaba guardado
    return (
        build_title(
            "YA ESTÁ EN MI LISTA",
            icon="ℹ️",
            indent=4,
        )
        + f"🎮 {game['name']}"
    )


def build_watchlist_message():
    # Construye /watchlist
    watchlist, _ = get_watchlist()

    if not watchlist:
        return "👀 Tu lista está vacía."

    lines = [
        build_title(
            "MI LISTADO DE JUEGOS",
            icon="👀",
            indent=12,
        ).rstrip(),
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

        # Formato actual
        if (
            platforms
            and isinstance(
                platforms[0],
                dict,
            )
        ):
            for platform in platforms:
                lines.append(
                    (
                        "      "
                        f"{platform['label']}"
                        " — "
                        f"{display_release_date(platform.get('release_date'))}"
                    )
                )

        # Compatibilidad con formato antiguo
        elif platforms:
            release_date = (
                display_release_date(
                    game.get(
                        "release_date"
                    )
                )
            )

            lines.append(
                (
                    "      "
                    f"{' | '.join(platforms)}"
                    " — "
                    f"{release_date}"
                )
            )

        else:
            release_date = (
                display_release_date(
                    game.get(
                        "release_date"
                    )
                )
            )

            lines.append(
                (
                    "      "
                    "Plataformas por confirmar"
                    " — "
                    f"{release_date}"
                )
            )

        lines.append("")

    return "\n".join(
        lines
    ).rstrip()


# ============================================================
# NEXT
# ============================================================

def parse_release_date(
    date_string,
):
    # Convierte YYYY-MM-DD a date
    if not date_string:
        return None

    try:
        return datetime.strptime(
            date_string,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return None


def get_upcoming_games():
    # Obtiene próximos juegos de la lista
    watchlist, _ = get_watchlist()

    today = datetime.now(
        MADRID_TIMEZONE
    ).date()

    upcoming_games = []

    for game in watchlist:
        platforms = game.get(
            "platforms",
            [],
        )

        future_releases = []

        # Fechas por plataforma
        if (
            platforms
            and isinstance(
                platforms[0],
                dict,
            )
        ):
            for platform in platforms:
                date_string = (
                    platform.get(
                        "release_date"
                    )
                )

                release_date = (
                    parse_release_date(
                        date_string
                    )
                )

                if (
                    not release_date
                    or release_date < today
                ):
                    continue

                future_releases.append(
                    {
                        "label":
                            platform["label"],

                        "date":
                            date_string,

                        "date_obj":
                            release_date,
                    }
                )

        # Compatibilidad con formato antiguo
        else:
            date_string = game.get(
                "release_date"
            )

            release_date = (
                parse_release_date(
                    date_string
                )
            )

            if (
                release_date
                and release_date >= today
            ):
                if platforms:
                    label = " | ".join(
                        platforms
                    )
                else:
                    label = (
                        "Plataformas por confirmar"
                    )

                future_releases.append(
                    {
                        "label":
                            label,

                        "date":
                            date_string,

                        "date_obj":
                            release_date,
                    }
                )

        if not future_releases:
            continue

        future_releases.sort(
            key=lambda release:
                release["date_obj"]
        )

        upcoming_games.append(
            {
                "name":
                    game["name"],

                "next_date":
                    future_releases[0][
                        "date_obj"
                    ],

                "releases":
                    future_releases,
            }
        )

    # Próximos juegos primero
    upcoming_games.sort(
        key=lambda game: (
            game["next_date"],
            game["name"].lower(),
        )
    )

    return upcoming_games[
        :NEXT_GAME_LIMIT
    ]


def build_next_message():
    # Construye /next
    upcoming_games = (
        get_upcoming_games()
    )

    if not upcoming_games:
        return (
            "⏭️ No tienes próximos "
            "lanzamientos con fecha."
        )

    lines = [
        build_title(
            "PRÓXIMOS LANZAMIENTOS",
            icon="⏭️",
            indent=10,
        ).rstrip(),
        "",
    ]

    for game in upcoming_games:
        lines.append(
            f"🎮 {game['name']}"
        )

        for release in game[
            "releases"
        ]:
            lines.append(
                (
                    "      "
                    f"{release['label']}"
                    " — "
                    f"{display_release_date(release['date'])}"
                )
            )

        lines.append("")

    return "\n".join(
        lines
    ).rstrip()


# ============================================================
# BOTONES
# ============================================================

def build_search_keyboard(
    games,
):
    # Botones con resultados de IGDB
    buttons = []

    for game in games:
        buttons.append(
            [
                {
                    "text":
                        game["name"],

                    "callback_data":
                        f"watch:{game['id']}",
                }
            ]
        )

    return {
        "inline_keyboard": buttons
    }


def build_unwatch_keyboard(
    watchlist,
):
    # Botones para eliminar juegos
    buttons = []

    for game in watchlist:
        buttons.append(
            [
                {
                    "text":
                        f"❌ {game['name']}",

                    "callback_data":
                        f"unwatch:{game['id']}",
                }
            ]
        )

    return {
        "inline_keyboard": buttons
    }


# ============================================================
# WATCHLIST
# ============================================================

def add_game_to_watchlist(
    game_id,
):
    # Obtiene el juego seleccionado
    game = get_igdb_game(
        game_id
    )

    if not game:
        return None, False

    watchlist, sha = get_watchlist()

    existing_game = next(
        (
            item
            for item in watchlist
            if item["id"] == game["id"]
        ),
        None,
    )

    # Devuelve el juego ya guardado
    if existing_game:
        return existing_game, False

    release_date = (
        format_release_date(
            game.get(
                "first_release_date"
            )
        )
    )

    platforms = build_platform_data(
        game
    )

    watchlist.append(
        {
            "id":
                game["id"],

            "name":
                game["name"],

            "release_date":
                release_date,

            "platforms":
                platforms,
        }
    )

    save_watchlist(
        watchlist,
        sha,
    )

    # Datos usados en el mensaje
    game["release_date"] = (
        release_date
    )

    game["platform_data"] = (
        platforms
    )

    return game, True


def remove_game_from_watchlist(
    game_id,
):
    # Elimina un juego de la lista
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


# ============================================================
# CALLBACKS
# ============================================================

def handle_watch_callback(
    chat_id,
    game_id,
):
    # Añade el juego elegido
    game, added = (
        add_game_to_watchlist(
            game_id
        )
    )

    if not game:
        send_huginn_message(
            chat_id,
            (
                "❌ No he podido "
                "encontrar el juego."
            ),
        )
        return

    if not added:
        send_huginn_message(
            chat_id,
            build_already_added_message(
                game
            ),
        )
        return

    send_huginn_message(
        chat_id,
        build_watch_added_message(
            game
        ),
    )


def handle_unwatch_callback(
    chat_id,
    game_id,
):
    # Elimina el juego elegido
    game, removed = (
        remove_game_from_watchlist(
            game_id
        )
    )

    if not removed:
        send_huginn_message(
            chat_id,
            (
                "ℹ️ Ese juego ya no está "
                "en tu lista."
            ),
        )
        return

    send_huginn_message(
        chat_id,
        (
            "🗑️ Eliminado de tu lista\n\n"
            f"🎮 {game['name']}"
        ),
    )


def handle_huginn_callback(
    callback,
):
    # Procesa botones de Huginn
    callback_id = callback.get(
        "id"
    )

    callback_data = callback.get(
        "data",
        "",
    )

    message = callback.get(
        "message",
        {},
    )

    chat_id = str(
        message
        .get("chat", {})
        .get("id", "")
    )

    if chat_id != HUGINN_CHAT_ID:
        return {
            "ok": True
        }

    if callback_id:
        answer_huginn_callback(
            callback_id
        )

    if callback_data.startswith(
        "watch:"
    ):
        game_id = int(
            callback_data.split(
                ":",
                1,
            )[1]
        )

        handle_watch_callback(
            chat_id,
            game_id,
        )

    elif callback_data.startswith(
        "unwatch:"
    ):
        game_id = int(
            callback_data.split(
                ":",
                1,
            )[1]
        )

        handle_unwatch_callback(
            chat_id,
            game_id,
        )

    return {
        "ok": True
    }


# ============================================================
# COMANDOS
# ============================================================

def handle_huginn_message(
    message,
):
    # Procesa comandos de Huginn
    chat_id = str(
        message
        .get("chat", {})
        .get("id", "")
    )

    text = message.get(
        "text",
        "",
    ).strip()

    if chat_id != HUGINN_CHAT_ID:
        return {
            "ok": True
        }

    # Ayuda
    if text == "/help":
        send_huginn_message(
            chat_id,
            build_help_message(),
        )

    # Próximos lanzamientos
    elif text == "/next":
        send_huginn_message(
            chat_id,
            build_next_message(),
        )

    # Mostrar lista
    elif text == "/watchlist":
        send_huginn_message(
            chat_id,
            build_watchlist_message(),
        )

    # Eliminar juego
    elif text == "/unwatch":
        watchlist, _ = (
            get_watchlist()
        )

        if not watchlist:
            send_huginn_message(
                chat_id,
                "👀 Tu lista está vacía.",
            )

        else:
            send_huginn_message(
                chat_id,
                (
                    "🗑️ ¿Qué juego "
                    "quieres eliminar?"
                ),
                build_unwatch_keyboard(
                    watchlist
                ),
            )

    # Buscar juego
    elif text.startswith(
        "/watch "
    ):
        search_term = text[
            len("/watch "):
        ].strip()

        if not search_term:
            send_huginn_message(
                chat_id,
                (
                    "Uso: /watch "
                    "nombre del juego"
                ),
            )

            return {
                "ok": True
            }

        games = search_igdb_games(
            search_term
        )

        if not games:
            send_huginn_message(
                chat_id,
                (
                    "❌ No he encontrado "
                    "ningún juego."
                ),
            )

        else:
            send_huginn_message(
                chat_id,
                build_watch_search_message(),
                build_search_keyboard(
                    games
                ),
            )

    # /watch sin nombre
    elif text == "/watch":
        send_huginn_message(
            chat_id,
            (
                "Uso: /watch "
                "nombre del juego"
            ),
        )

    return {
        "ok": True
    }


# ============================================================
# ENTRADA
# ============================================================

def handle_huginn_update(
    update,
):
    # Entrada principal de Huginn
    callback = update.get(
        "callback_query"
    )

    if isinstance(
        callback,
        dict,
    ):
        return handle_huginn_callback(
            callback
        )

    message = update.get(
        "message"
    )

    if isinstance(
        message,
        dict,
    ):
        return handle_huginn_message(
            message
        )

    return {
        "ok": True
    }
