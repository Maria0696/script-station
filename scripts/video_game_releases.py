import os
import requests
from html import escape
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Credenciales desde GitHub Secrets
CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Zona horaria usada para definir "hoy"
MADRID_TZ = ZoneInfo("Europe/Madrid")

# IDs de plataformas de IGDB y nombre mostrado en Telegram
PLATFORM_LABELS = {
    167: "🔵 PS5",
    508: "🔴 Switch 2",
    6: "💻 PC",
    169: "🟢 Xbox Series",
    48: "🔵 PS4",
    49: "🟢 Xbox One",
    130: "🔴 Switch",
    390: "🥽 PS VR2",
    471: "🥽 Meta Quest",  # Meta Quest 3
    386: "🥽 Meta Quest",  # Meta Quest 2
    163: "🥽 SteamVR",
}

# Orden en el que se muestran las plataformas
PLATFORM_ORDER = [
    167,  # PS5
    508,  # Switch 2
    6,    # PC
    169,  # Xbox Series
    48,   # PS4
    49,   # Xbox One
    130,  # Switch
    390,  # PlayStation VR2
    471,  # Meta Quest 3
    386,  # Meta Quest 2
    163,  # SteamVR
]

# Regiones válidas si IGDB informa una región
VALID_REGIONS = {
    "europe",
    "worldwide",
}

# Criterios para marcar un juego con ⭐
FEATURED_HYPES_MIN = 25
FEATURED_RATING_COUNT_MIN = 100
MAX_FEATURED_GAMES = 3

# Dejamos margen respecto al límite de Telegram
MAX_TELEGRAM_LENGTH = 3900

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

def get_releases_today(token):
    # Fecha actual según Madrid
    today = datetime.now(MADRID_TZ).date()

    # Inicio del día
    start_datetime = datetime(
        today.year,
        today.month,
        today.day,
        0,
        0,
        0,
        tzinfo=MADRID_TZ,
    )

    # Inicio del día siguiente
    end_datetime = start_datetime + timedelta(days=1)

    # IGDB trabaja con timestamps Unix
    start_ts = int(start_datetime.timestamp())
    end_ts = int(end_datetime.timestamp())

    # IDs de plataformas para la consulta
    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    # Busca lanzamientos e información de popularidad
    query = f"""
    fields
        game.id,
        game.name,
        game.hypes,
        game.total_rating_count,
        platform,
        release_region.region,
        date,
        human;

    where date >= {start_ts}
        & date < {end_ts}
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

    # Log útil si IGDB devuelve error
    if not response.ok:
        print(f"IGDB error: {response.status_code}")
        print(response.text)

    response.raise_for_status()

    releases = response.json()

    print(f"IGDB releases received: {len(releases)}")

    # Agrupa lanzamientos del mismo juego por plataforma
    games = filter_and_group_releases(releases)

    # Decide qué juegos llevan ⭐
    return mark_featured_games(games)


def filter_and_group_releases(releases):
    games = {}

    for release in releases:
        region = release.get("release_region")

        # Si hay región, solo aceptamos Europa o Worldwide
        if isinstance(region, dict):
            region_name = region.get("region", "").lower()

            if (
                region_name
                and region_name not in VALID_REGIONS
            ):
                continue

        game = release.get("game")

        # Ignora registros sin datos válidos del juego
        if not isinstance(game, dict):
            continue

        game_id = game.get("id")
        game_name = game.get("name")
        platform_id = release.get("platform")

        # Ignora datos incompletos o plataformas no usadas
        if (
            not game_id
            or not game_name
            or platform_id not in PLATFORM_LABELS
        ):
            continue

        # Crea el juego si aún no existe
        if game_id not in games:
            games[game_id] = {
                "name": game_name,
                "platforms": set(),
                "hypes": game.get("hypes", 0) or 0,
                "rating_count": game.get("total_rating_count", 0) or 0,
                "featured": False,
            }

        # Añade la plataforma evitando duplicados
        games[game_id]["platforms"].add(platform_id)

    print(f"Games to send: {len(games)}")

    return list(games.values())

def get_importance_score(game):
    # Da más peso al interés previo al lanzamiento
    return (
        game["hypes"] * 5
        + game["rating_count"]
    )

def mark_featured_games(games):
    # Juegos que cumplen un mínimo de relevancia
    candidates = [
        game
        for game in games
        if (
            game["hypes"] >= FEATURED_HYPES_MIN
            or game["rating_count"] >= FEATURED_RATING_COUNT_MIN
        )
    ]

    # Ordena candidatos por relevancia
    candidates.sort(
        key=get_importance_score,
        reverse=True,
    )

    # Máximo 3 destacados al día
    for game in candidates[:MAX_FEATURED_GAMES]:
        game["featured"] = True

    print(
        f"Featured games: "
        f"{sum(game['featured'] for game in games)}"
    )

    # Destacados primero; después, orden alfabético
    return sorted(
        games,
        key=lambda game: (
            not game["featured"],
            -get_importance_score(game)
            if game["featured"]
            else 0,
            game["name"].lower(),
        ),
    )

def get_platform_labels(platform_ids):
    platforms = []

    # Convierte IDs en nombres visibles
    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[platform_id]

        # Evita duplicar Meta Quest
        if label not in platforms:
            platforms.append(label)

    return platforms

def build_messages(games):
    # Fecha mostrada en Telegram
    today = datetime.now(MADRID_TZ).strftime("%d-%m-%Y")

    header = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "         🚀 <b>NEW GAMES OUT TODAY</b>\n"
        f"                         {today}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # Mensaje si no hay lanzamientos
    if not games:
        return [
            header + "No releases found today."
        ]

    messages = []
    current_message = header

    for game in games:
        # Escapa caracteres especiales para HTML
        game_name = escape(game["name"])

        platforms = get_platform_labels(
            game["platforms"]
        )

        # Añade ⭐ solo a los juegos destacados
        star = "⭐ " if game["featured"] else ""

        game_block = (
            f"{star}<b>{game_name}</b>\n"
            f"   {' | '.join(platforms)}\n\n"
        )

        # Crea otro mensaje si nos acercamos al límite
        if (
            len(current_message) + len(game_block)
            > MAX_TELEGRAM_LENGTH
        ):
            messages.append(current_message.rstrip())
            current_message = header + game_block
        else:
            current_message += game_block

    # Añade el último bloque pendiente
    if current_message.strip():
        messages.append(current_message.rstrip())

    return messages

def send_telegram(text):
    # Envía un mensaje al chat de Telegram
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=30,
    )

    # Log útil si Telegram devuelve error
    if not response.ok:
        print(f"Telegram error: {response.status_code}")
        print(response.text)

    response.raise_for_status()

def main():
    # 1. Autenticación con IGDB
    token = get_access_token()

    # 2. Obtener lanzamientos de hoy
    games = get_releases_today(token)

    # 3. Construir uno o varios mensajes
    messages = build_messages(games)

    # 4. Enviar mensajes a Telegram
    for message in messages:
        send_telegram(message)

# Ejecuta main solo si lanzamos este archivo directamente
if __name__ == "__main__":
    main()
