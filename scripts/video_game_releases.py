import os
import requests
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo

CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MADRID_TZ = ZoneInfo("Europe/Madrid")

# IDs oficiales de plataformas en IGDB
PLATFORM_LABELS = {
    167: "🔵 PS5",
    508: "🔴 Switch 2",
    6: "💻 PC",
    169: "🟢 Xbox Series",
    48: "🔵 PS4",
    49: "🟢 Xbox One",
    130: "🔴 Switch",
}

PLATFORM_ORDER = [
    167,  # PS5
    508,  # Switch 2
    6,    # PC
    169,  # Xbox Series
    48,   # PS4
    49,   # Xbox One
    130,  # Switch
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
    }

def get_releases_today(token):
    today = datetime.now(MADRID_TZ).date()

    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    query = f"""
    fields
        game.id,
        game.name,
        platform,
        release_region.region;

    where y = {today.year}
        & m = {today.month}
        & d = {today.day}
        & platform = ({platform_ids});

    limit 500;
    """

    response = requests.post(
        "https://api.igdb.com/v4/release_dates",
        headers=get_igdb_headers(token),
        data=query,
        timeout=30,
    )

    response.raise_for_status()

    releases = response.json()

    return filter_and_group_releases(releases)


def filter_and_group_releases(releases):
    games = {}

    for release in releases:
        region = release.get("release_region")

        if not isinstance(region, dict):
            continue

        region_name = region.get("region", "").lower()

        if region_name not in VALID_REGIONS:
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

    return sorted(
        games.values(),
        key=lambda game: game["name"].lower(),
    )


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

        platforms = [
            PLATFORM_LABELS[platform_id]
            for platform_id in PLATFORM_ORDER
            if platform_id in game["platforms"]
        ]

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
