# Informe diario de lanzamientos por Huginn (videogames.yml, cada mañana).
# Juegos que salen hoy en las plataformas soportadas, con hasta 3 destacados
# (⭐) según su popularidad en IGDB.

import logging
from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from core import igdb
from core.config import PLATFORM_LABELS, PLATFORM_ORDER
from core.logs import configure_logging
from core.notifications import notifications

logger = logging.getLogger(__name__)

# "Hoy" es el día de Madrid, no el de UTC
MADRID_TZ = ZoneInfo("Europe/Madrid")


# IDs de popularity_types de IGDB: visitas a su web y "quiero jugarlo"
POPULARITY_VISITS = 1
POPULARITY_WANT_TO_PLAY = 2


# Puntuación = 0.4 · visitas + 0.6 · quiero jugarlo. Pesa más el interés
# declarado que las visitas
VISITS_WEIGHT = 0.4
WANT_TO_PLAY_WEIGHT = 0.6


# Destacado (⭐): puntuación >= 75 % de la mejor del día y por encima de un
# mínimo absoluto, para no destacar nada un día sin lanzamientos relevantes
FEATURED_SCORE_MIN = 0.00002
FEATURED_RELATIVE_THRESHOLD = 0.75
MAX_FEATURED_GAMES = 3


# Los valores de IGDB son muy pequeños: solo para leerlos en los logs
LOG_SCORE_MULTIPLIER = 1_000_000


# Telegram admite 4096 caracteres por mensaje; el informe se parte antes
MAX_TELEGRAM_LENGTH = 3900


def get_releases_today():
    today = datetime.now(MADRID_TZ).date()

    start_datetime = datetime(
        today.year, today.month, today.day, 0, 0, 0, tzinfo=MADRID_TZ
    )

    end_datetime = start_datetime + timedelta(days=1)

    start_ts = int(start_datetime.timestamp())

    end_ts = int(end_datetime.timestamp())

    releases = igdb.get_releases_between(start_ts, end_ts)

    logger.info("IGDB releases received: %d", len(releases))

    return filter_and_group_releases(releases)


def filter_and_group_releases(releases):
    games = {}

    for release in releases:
        if not igdb.is_valid_region(release):
            continue

        game = release.get("game")

        if not isinstance(game, dict):
            continue

        game_id = game.get("id")

        game_name = game.get("name")

        platform_id = release.get("platform")

        if not game_id or not game_name or platform_id not in PLATFORM_LABELS:
            continue

        if game_id not in games:
            games[game_id] = {
                "id": game_id,
                "name": game_name,
                "platforms": set(),
                "visits": 0.0,
                "want_to_play": 0.0,
                "popularity_score": 0.0,
                "featured": False,
            }

        games[game_id]["platforms"].add(platform_id)

    logger.info("Games to send: %d", len(games))

    return list(games.values())


def add_popularity_data(games):
    if not games:
        return games

    popularity_data = igdb.get_popularity_primitives(
        [game["id"] for game in games], [POPULARITY_VISITS, POPULARITY_WANT_TO_PLAY]
    )

    logger.info("Popularity records received: %d", len(popularity_data))

    games_by_id = {game["id"]: game for game in games}

    for item in popularity_data:
        game_id = item.get("game_id")

        popularity_type = item.get("popularity_type")

        value = float(item.get("value", 0) or 0)

        if game_id not in games_by_id:
            continue

        game = games_by_id[game_id]

        if popularity_type == POPULARITY_VISITS:
            game["visits"] = value

        elif popularity_type == POPULARITY_WANT_TO_PLAY:
            game["want_to_play"] = value

    for game in games:
        game["popularity_score"] = (
            game["visits"] * VISITS_WEIGHT + game["want_to_play"] * WANT_TO_PLAY_WEIGHT
        )

    return games


def mark_featured_games(games):
    if not games:
        return games

    # Detalle de popularidad con DEBUG=true
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("PopScore data:")

        for game in sorted(
            games, key=lambda game: game["popularity_score"], reverse=True
        ):
            display_score = game["popularity_score"] * LOG_SCORE_MULTIPLIER

            logger.debug("- %s | Score: %.2f", game["name"], display_score)

    best_score = max(game["popularity_score"] for game in games)

    relative_min = best_score * FEATURED_RELATIVE_THRESHOLD

    featured_threshold = max(FEATURED_SCORE_MIN, relative_min)

    logger.info("Featured threshold: %.2f", featured_threshold * LOG_SCORE_MULTIPLIER)

    candidates = [
        game for game in games if (game["popularity_score"] >= featured_threshold)
    ]

    candidates.sort(key=lambda game: game["popularity_score"], reverse=True)

    for game in candidates[:MAX_FEATURED_GAMES]:
        game["featured"] = True

    logger.info("Featured games: %d", sum(game["featured"] for game in games))

    return sorted(
        games,
        key=lambda game: (
            not game["featured"],
            (-game["popularity_score"] if game["featured"] else 0),
            game["name"].lower(),
        ),
    )


def get_platform_labels(platform_ids):
    platforms = []

    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[platform_id]

        if label not in platforms:
            platforms.append(label)

    return platforms


def build_messages(games):
    today = datetime.now(MADRID_TZ).strftime("%d-%m-%Y")

    header = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "         🚀 <b>NEW GAMES OUT TODAY</b>\n"
        f"                         {today}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not games:
        return [(header + "No releases found today.")]

    messages = []
    current_message = header

    for game in games:
        game_name = escape(game["name"])

        platforms = get_platform_labels(game["platforms"])

        star = "⭐ " if game["featured"] else ""

        game_block = f"{star}<b>{game_name}</b>\n   {' | '.join(platforms)}\n\n"

        if len(current_message) + len(game_block) > MAX_TELEGRAM_LENGTH:
            messages.append(current_message.rstrip())

            current_message = header + game_block

        else:
            current_message += game_block

    if current_message.strip():
        messages.append(current_message.rstrip())

    return messages


def send_notification(text):
    return notifications.huginn(text, parse_mode="HTML")


def main():
    configure_logging()

    games = get_releases_today()
    games = add_popularity_data(games)
    games = mark_featured_games(games)

    for message in build_messages(games):
        send_notification(message)


if __name__ == "__main__":  # pragma: no cover
    main()
