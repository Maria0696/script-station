import json
import os
import requests
from datetime import datetime
from pathlib import Path


# Credenciales desde GitHub Secrets
CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# Archivo donde guardamos la watchlist
WATCHLIST_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "watchlist.json"
)


# IDs de plataformas de IGDB
PLATFORM_LABELS = {
    167: "🔵 PS5",
    508: "🔴 Switch 2",
    6: "💻 PC",
    169: "🟢 Xbox Series",
    48: "🔵 PS4",
    49: "🟢 Xbox One",
    130: "🔴 Switch",
    390: "🥽 PS VR2",
    471: "🥽 Meta Quest",
    386: "🥽 Meta Quest",
    163: "🥽 SteamVR",
}


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


# Regiones válidas
VALID_REGIONS = {
    "europe",
    "worldwide",
}


def get_access_token():
    # Obtiene token temporal de Twitch para usar IGDB
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["access_token"]


def get_igdb_headers(token):
    # Cabeceras necesarias para consultar IGDB
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def load_watchlist():
    # Lee la watchlist del repositorio
    if not WATCHLIST_PATH.exists():
        return []

    with open(
        WATCHLIST_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_watchlist(watchlist):
    # Guarda la watchlist actualizada
    with open(
        WATCHLIST_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            watchlist,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")


def get_games_from_igdb(token, game_ids):
    # Consulta datos básicos de los juegos
    if not game_ids:
        return {}

    ids = ",".join(
        str(game_id)
        for game_id in game_ids
    )

    query = f"""
    fields
        id,
        name,
        first_release_date,
        platforms;
    where id = ({ids});
    limit 500;
    """

    response = requests.post(
        "https://api.igdb.com/v4/games",
        headers=get_igdb_headers(token),
        data=query,
        timeout=30,
    )

    response.raise_for_status()

    return {
        game["id"]: game
        for game in response.json()
    }


def get_release_dates_from_igdb(token, game_ids):
    # Consulta fechas por juego y plataforma
    if not game_ids:
        return {}

    ids = ",".join(
        str(game_id)
        for game_id in game_ids
    )

    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    query = f"""
    fields
        game,
        platform,
        date,
        release_region.region;

    where game = ({ids})
        & platform = ({platform_ids});

    limit 500;
    sort date asc;
    """

    response = requests.post(
        "https://api.igdb.com/v4/release_dates",
        headers=get_igdb_headers(token),
        data=query,
        timeout=30,
    )

    response.raise_for_status()

    result = {}

    for release in response.json():
        game_id = release.get("game")
        platform_id = release.get("platform")
        region = release.get("release_region")

        if isinstance(game_id, dict):
            game_id = game_id.get("id")

        if platform_id not in PLATFORM_LABELS:
            continue

        # Solo Europa, Worldwide o sin región
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

        release_date = timestamp_to_date(
            release.get("date")
        )

        if not release_date:
            continue

        game_dates = result.setdefault(
            game_id,
            {},
        )

        # Conserva la primera fecha válida
        if platform_id not in game_dates:
            game_dates[platform_id] = release_date

    return result


def timestamp_to_date(timestamp):
    # Convierte timestamp de IGDB a YYYY-MM-DD
    if not timestamp:
        return None

    return datetime.utcfromtimestamp(
        timestamp
    ).date().isoformat()


def display_date(date_string):
    # Convierte YYYY-MM-DD a DD-MM-YYYY
    if not date_string:
        return "Sin fecha"

    return datetime.strptime(
        date_string,
        "%Y-%m-%d",
    ).strftime("%d-%m-%Y")


def send_telegram(text):
    # Envía un aviso a Telegram
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=30,
    )

    response.raise_for_status()


def build_platforms(game, release_dates):
    # Construye las plataformas actuales
    platform_ids = set(
        game.get(
            "platforms",
            [],
        )
    )

    platform_ids.update(
        release_dates.keys()
    )

    platforms = []
    labels_added = set()

    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[platform_id]

        # Evita Meta Quest duplicado
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


def build_change_message(
    game_name,
    platform_label,
    old_date,
    new_date,
):
    # Se anuncia una fecha nueva
    if old_date is None and new_date is not None:
        return (
            "📅 NUEVA FECHA DE LANZAMIENTO\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n"
            f"📅 {display_date(new_date)}"
        )

    # Se retira una fecha existente
    if old_date is not None and new_date is None:
        return (
            "⚠️ FECHA DE LANZAMIENTO RETIRADA\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n\n"
            f"Antes: {display_date(old_date)}\n"
            "Ahora: Por confirmar"
        )

    old_datetime = datetime.strptime(
        old_date,
        "%Y-%m-%d",
    )

    new_datetime = datetime.strptime(
        new_date,
        "%Y-%m-%d",
    )

    # Nueva fecha posterior
    if new_datetime > old_datetime:
        title = "⏳ RETRASO DE LANZAMIENTO"

    # Nueva fecha anterior
    elif new_datetime < old_datetime:
        title = "⏩ ADELANTO DE LANZAMIENTO"

    else:
        return None

    return (
        f"{title}\n\n"
        f"🎮 {game_name}\n"
        f"{platform_label}\n\n"
        f"Antes: {display_date(old_date)}\n"
        f"Ahora: {display_date(new_date)}"
    )


def monitor_watchlist():
    # Carga los juegos que seguimos
    watchlist = load_watchlist()

    if not watchlist:
        print("Watchlist is empty.")
        return False

    token = get_access_token()

    game_ids = [
        game["id"]
        for game in watchlist
    ]

    # Datos actuales de IGDB
    igdb_games = get_games_from_igdb(
        token,
        game_ids,
    )

    release_dates = get_release_dates_from_igdb(
        token,
        game_ids,
    )

    changes_found = False

    for item in watchlist:
        game_id = item["id"]

        igdb_game = igdb_games.get(
            game_id
        )

        if not igdb_game:
            print(
                f"Game not found: "
                f"{item['name']} ({game_id})"
            )
            continue

        # Actualiza nombre y fecha general
        item["name"] = igdb_game.get(
            "name",
            item["name"],
        )

        item["release_date"] = timestamp_to_date(
            igdb_game.get(
                "first_release_date"
            )
        )

        current_platforms = build_platforms(
            igdb_game,
            release_dates.get(
                game_id,
                {},
            ),
        )

        stored_platforms = item.get(
            "platforms",
            [],
        )

        # Migra silenciosamente el formato antiguo
        if (
            not stored_platforms
            or not isinstance(
                stored_platforms[0],
                dict,
            )
        ):
            item["platforms"] = current_platforms
            changes_found = True

            print(
                f"Migrated platforms: "
                f"{item['name']}"
            )

            continue

        old_by_id = {
            platform["id"]: platform
            for platform in stored_platforms
        }

        current_by_id = {
            platform["id"]: platform
            for platform in current_platforms
        }

        # Comprueba cambios de fecha por plataforma
        for platform_id in (
            old_by_id.keys()
            & current_by_id.keys()
        ):
            old_platform = old_by_id[
                platform_id
            ]

            new_platform = current_by_id[
                platform_id
            ]

            old_date = old_platform.get(
                "release_date"
            )

            new_date = new_platform.get(
                "release_date"
            )

            if old_date == new_date:
                continue

            message = build_change_message(
                item["name"],
                new_platform["label"],
                old_date,
                new_date,
            )

            if message:
                send_telegram(message)

            print(
                f"Date changed: "
                f"{item['name']} | "
                f"{new_platform['label']} | "
                f"{old_date} -> {new_date}"
            )

            changes_found = True

        # Actualiza siempre el listado de plataformas
        if stored_platforms != current_platforms:
            item["platforms"] = current_platforms
            changes_found = True

    # Solo guarda el JSON si hubo cambios
    if changes_found:
        save_watchlist(watchlist)

    return changes_found


def main():
    # Comprueba cambios en toda la watchlist
    monitor_watchlist()


if __name__ == "__main__":
    main()
