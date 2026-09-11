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
    169,  # Xbox Series X|S
    48,   # PS4
    49,   # Xbox One
    130,  # Switch
]

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


def get_games_released_today(token):
    today = datetime.now(MADRID_TZ).date()

    start_ts = int(
        datetime.combine(
            today,
            datetime.min.time(),
            tzinfo=MADRID_TZ,
        ).timestamp()
    )

    end_ts = int(
        datetime.combine(
            today,
            datetime.max.time(),
            tzinfo=MADRID_TZ,
        ).timestamp()
    )

    query = f"""
    fields
        name,
        first_release_date,
        platforms.id,
        platforms.name;
    where first_release_date >= {start_ts} & first_release_date <= {end_ts};
    limit 100;
    sort first_release_date asc;
    """

    response = requests.post(
        "https://api.igdb.com/v4/games",
        headers={
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        data=query,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def build_message(games):
    today = datetime.now(MADRID_TZ).strftime("%d-%m-%Y")

    header = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "         🚀 <b>NEW GAMES OUT TODAY</b>\n"
        f"                         {today}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not games:
        return header + "No releases found today."

    message = header

    for game in games:
        game_name = escape(game["name"])

        game_platform_ids = {
            platform.get("id")
            for platform in game.get("platforms", [])
            if platform.get("id") in PLATFORM_LABELS
        }

        platforms = [
            PLATFORM_LABELS[platform_id]
            for platform_id in PLATFORM_ORDER
            if platform_id in game_platform_ids
        ]

        message += f"<b>{game_name}</b>\n"

        if platforms:
            message += f"   {' | '.join(platforms)}\n"

        message += "\n"

    return message[:4000]


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

    games = get_games_released_today(token)

    message = build_message(games)

    send_telegram(message)


if __name__ == "__main__":
    main()
