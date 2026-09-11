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
    # Consulta todos los juegos de la watchlist
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
        first_release_date;
    where id = ({ids});
    limit 500;
    """

    response = requests.post(
        "https://api.igdb.com/v4/games",
        headers=get_igdb_headers(token),
        data=query,
        timeout=30,
    )

    # Log útil si IGDB devuelve error
    if not response.ok:
        print(f"IGDB error: {response.status_code}")
        print(response.text)

    response.raise_for_status()

    games = response.json()

    # Devuelve los juegos indexados por ID
    return {
        game["id"]: game
        for game in games
    }


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
    # Envía un aviso al chat de Telegram
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=30,
    )

    # Log útil si Telegram devuelve error
    if not response.ok:
        print(f"Telegram error: {response.status_code}")
        print(response.text)

    response.raise_for_status()


def build_change_message(
    game_name,
    old_date,
    new_date,
):
    # Nueva fecha para un juego que no la tenía
    if old_date is None and new_date is not None:
        return (
            "📅 NUEVA FECHA DE LANZAMIENTO\n\n"
            f"🎮 {game_name}\n"
            f"📅 {display_date(new_date)}"
        )

    # IGDB retira una fecha existente
    if old_date is not None and new_date is None:
        return (
            "⚠️ FECHA DE LANZAMIENTO RETIRADA\n\n"
            f"🎮 {game_name}\n"
            f"Antes: {display_date(old_date)}\n"
            "Ahora: Por confirmar"
        )

    # Convierte las fechas para compararlas
    old_datetime = datetime.strptime(
        old_date,
        "%Y-%m-%d",
    )

    new_datetime = datetime.strptime(
        new_date,
        "%Y-%m-%d",
    )

    # Nueva fecha posterior: retraso
    if new_datetime > old_datetime:
        title = "⏳ RETRASO DE LANZAMIENTO"

    # Nueva fecha anterior: adelanto
    elif new_datetime < old_datetime:
        title = "⏩ ADELANTO DE LANZAMIENTO"

    else:
        return None

    return (
        f"{title}\n\n"
        f"🎮 {game_name}\n\n"
        f"Antes: {display_date(old_date)}\n"
        f"Ahora: {display_date(new_date)}"
    )


def monitor_watchlist():
    # Carga los juegos que estamos siguiendo
    watchlist = load_watchlist()

    if not watchlist:
        print("Watchlist is empty.")
        return False

    # Autenticación con IGDB
    token = get_access_token()

    game_ids = [
        game["id"]
        for game in watchlist
    ]

    # Obtiene los datos actuales de IGDB
    igdb_games = get_games_from_igdb(
        token,
        game_ids,
    )

    changes_found = False

    for item in watchlist:
        game_id = item["id"]

        igdb_game = igdb_games.get(game_id)

        # Ignora juegos que IGDB no devuelve
        if not igdb_game:
            print(
                f"Game not found in IGDB: "
                f"{item['name']} ({game_id})"
            )
            continue

        # Actualiza el nombre si cambia en IGDB
        item["name"] = igdb_game.get(
            "name",
            item["name"],
        )

        old_date = item.get("release_date")

        new_date = timestamp_to_date(
            igdb_game.get("first_release_date")
        )

        # No hace nada si la fecha sigue igual
        if old_date == new_date:
            continue

        # Construye y envía el aviso
        message = build_change_message(
            item["name"],
            old_date,
            new_date,
        )

        if message:
            send_telegram(message)

        # Guarda la nueva fecha
        item["release_date"] = new_date

        changes_found = True

        print(
            f"Date changed: {item['name']} | "
            f"{old_date} -> {new_date}"
        )

    # Solo modifica el JSON si hubo cambios
    if changes_found:
        save_watchlist(watchlist)

    return changes_found


def main():
    # Comprueba cambios en toda la watchlist
    monitor_watchlist()


# Ejecuta main solo al lanzar este archivo directamente
if __name__ == "__main__":
    main()
