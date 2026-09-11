import os
import requests
from html import escape
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MADRID_TZ = ZoneInfo("Europe/Madrid")

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

VALID_REGIONS = {
    "europe",
    "worldwide",
}

MAX_TELEGRAM_LENGTH = 3900

def get_access_token():
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
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

def get_releases_today(token):
    today = datetime.now(MADRID_TZ).date()

    start_datetime = datetime(
        today.year,
        today.month,
        today.day,
        0,
        0,
        0,
        tzinfo=MADRID_TZ,
    )

    end_datetime = start_datetime + timedelta(days=1)

    start_ts = int(start_datetime.timestamp())
    end_ts = int(end_datetime.timestamp())

    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    query = f"""
    fields
        game.id,
        game.name,
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

    print(f"Date used: {today}")
    print(f"Start timestamp: {start_ts}")
    print(f"End timestamp: {end_ts}")
    print("IGDB query:")
    print(query)

    response = requests.post(
        "https://api.igdb.com/v4/release_dates",
        headers=get_igdb_headers(token),
        data=query,
        timeout=30,
    )

    if not response.ok:
        print(response.status_code)
        print(response.text)

    response.raise_for_status()

    releases = response.json()

    print(f"Releases received from IGDB: {len(releases)}")
    print(releases)

    return filter_and_group_releases(releases)

def filter_and_group_releases(releases):
    games = {}

    for release in releases:
        region = release.get("release_region")

        # Si IGDB especifica región, solo aceptamos Europe o Worldwide.
        # Si no indica región, aceptamos el lanzamiento.
        if isinstance(region, dict):
            region_name = region.get("region", "").lower()

            if (
                region_name
                and region_name not in VALID_REGIONS
            ):
                continue

        game = release.get("game")

        if not isinstance(game, dict):
            continue

        game_id = game.get("id")
        game_name = game.get("name")
        platform_id = release.get("platform")

        if (
            not game_id
            or not game_name
            or platform_id not in PLATFORM_LABELS
        ):
            continue

        if game_id not in games:
            games[game_id] = {
                "name": game_name,
                "platforms": set(),
            }

        games[game_id]["platforms"].add(platform_id)

    print(f"Games after filtering: {len(games)}")

    return sorted(
        games.values(),
        key=lambda game: game["name"].lower(),
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
        return [
            header + "No releases found today."
        ]

    messages = []
    current_message = header

    for game in games:
        game_name = escape(game["name"])

        platforms = get_platform_labels(
            game["platforms"]
        )

        game_block = (
            f"<b>{game_name}</b>\n"
            f"   {' | '.join(platforms)}\n\n"
        )

        if (
            len(current_message) + len(game_block)
            > MAX_TELEGRAM_LENGTH
        ):
            messages.append(current_message.rstrip())
            current_message = header + game_block
        else:
            current_message += game_block

    if current_message.strip():
        messages.append(current_message.rstrip())

    return messages

def send_telegram(text):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=30,
    )

    if not response.ok:
        print(response.status_code)
        print(response.text)

    response.raise_for_status()

def main():
    token = get_access_token()

    games = get_releases_today(token)

    messages = build_messages(games)

    for message in messages:
        send_telegram(message)

if __name__ == "__main__":
    main()
