import logging

from core import github, igdb
from core.logs import configure_logging
from core.notifications import notifications

logger = logging.getLogger(__name__)


def load_watchlist():
    # Lee la watchlist y su sha desde GitHub
    return github.get_watchlist()


def save_watchlist(watchlist, sha):
    # Guarda la watchlist en GitHub con un commit
    github.save_watchlist(
        watchlist, sha, message=("chore: update watchlist release dates")
    )


def send_notification(text):
    # Publica un cambio de lanzamiento
    return notifications.emit("game.release_changed", text)


def build_change_message(
    game_name,
    platform_label,
    old_date,
    new_date,
    old_precision="day",
    new_precision="day",
):
    # Compara periodos, no días sueltos: "2027" -> 15-03-2027
    # es una fecha concretada, no un adelanto
    old_text = igdb.display_release_date(old_date, old_precision)
    new_text = igdb.display_release_date(new_date, new_precision)

    # Se anuncia una fecha nueva
    if old_date is None and new_date is not None:
        return (
            "📅 NUEVA FECHA DE LANZAMIENTO\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n"
            f"📅 {new_text}"
        )

    # Se retira una fecha existente
    if old_date is not None and new_date is None:
        return (
            "⚠️ FECHA DE LANZAMIENTO RETIRADA\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n\n"
            f"Antes: {old_text}\n"
            "Ahora: Por confirmar"
        )

    old_start, old_end = igdb.release_period(old_date, old_precision)
    new_start, new_end = igdb.release_period(new_date, new_precision)

    if new_start > old_end:
        title = "⏳ RETRASO DE LANZAMIENTO"

    elif new_end < old_start:
        title = "⏩ ADELANTO DE LANZAMIENTO"

    # Mismo periodo con más detalle: "2027" -> "Marzo 2027"
    elif igdb.is_more_precise(new_precision, old_precision):
        title = "📅 FECHA CONCRETADA"

    # Mismo periodo con menos detalle: 12-02-2027 -> "2027"
    elif igdb.is_more_precise(old_precision, new_precision):
        title = "⚠️ FECHA MENOS CONCRETA"

    else:
        return None

    return (
        f"{title}\n\n"
        f"🎮 {game_name}\n"
        f"{platform_label}\n\n"
        f"Antes: {old_text}\n"
        f"Ahora: {new_text}"
    )


def monitor_watchlist():
    # Carga los juegos que seguimos
    watchlist, sha = load_watchlist()

    if not watchlist:
        logger.info("Watchlist is empty.")

        return False

    game_ids = [game["id"] for game in watchlist]

    # Datos actuales de IGDB
    igdb_games = igdb.get_igdb_games(game_ids)

    release_dates = igdb.get_release_dates(game_ids)

    changes_found = False
    pending_messages = []

    for item in watchlist:
        game_id = item["id"]

        igdb_game = igdb_games.get(game_id)

        if not igdb_game:
            logger.warning("Game not found: %s (%s)", item["name"], game_id)

            continue

        # Actualiza nombre y fecha general
        item["name"] = igdb_game.get("name", item["name"])

        item["release_date"] = igdb.format_release_date(
            igdb_game.get("first_release_date")
        )

        current_platforms = igdb.build_platform_data(
            igdb_game, release_dates.get(game_id, {})
        )

        stored_platforms = item.get("platforms", [])

        # Migra silenciosamente el formato antiguo
        if not stored_platforms or not isinstance(stored_platforms[0], dict):
            item["platforms"] = current_platforms

            changes_found = True

            logger.info("Migrated platforms: %s", item["name"])

            continue

        old_by_id = {platform["id"]: platform for platform in stored_platforms}

        current_by_id = {platform["id"]: platform for platform in current_platforms}

        # Comprueba cambios de fecha por plataforma
        for platform_id in old_by_id.keys() & current_by_id.keys():
            old_platform = old_by_id[platform_id]

            new_platform = current_by_id[platform_id]

            old_date = old_platform.get("release_date")
            new_date = new_platform.get("release_date")

            old_precision = igdb.get_platform_precision(old_platform)
            new_precision = igdb.get_platform_precision(new_platform)

            # Los datos guardados sin precisión se actualizan sin avisar
            legacy = "date_precision" not in old_platform

            if old_date == new_date and (legacy or old_precision == new_precision):
                continue

            message = build_change_message(
                item["name"],
                new_platform["label"],
                old_date,
                new_date,
                old_precision,
                new_precision,
            )

            if message:
                pending_messages.append(message)

            logger.info(
                "Date changed: %s | %s | %s (%s) -> %s (%s)",
                item["name"],
                new_platform["label"],
                old_date,
                old_precision,
                new_date,
                new_precision,
            )

            changes_found = True

        # Actualiza siempre el listado de plataformas
        if stored_platforms != current_platforms:
            item["platforms"] = current_platforms

            changes_found = True

    # Solo guarda el JSON si hubo cambios
    if changes_found:
        save_watchlist(watchlist, sha)

    # Avisa solo cuando el cambio ya está guardado:
    # si el guardado falla, el aviso no se repite cada día
    for message in pending_messages:
        send_notification(message)

    return changes_found


def main():
    configure_logging()

    # Comprueba cambios en toda la watchlist
    monitor_watchlist()


if __name__ == "__main__":  # pragma: no cover
    main()
