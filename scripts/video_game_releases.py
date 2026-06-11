import os
from datetime import datetime, timezone

import requests

CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


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
    today = datetime.now(timezone.utc).date()

    start_ts = int(
        datetime.combine(
            today,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).timestamp()
    )

    end_ts = int(
        datetime.combine(
            today,
            datetime.max.time(),
            tzinfo=timezone.utc,
        ).timestamp()
    )

    query = f"""
    fields name,
           first_release_date,
           platforms.name;
    where first_release_date >= {start_ts}
      & first_release_date <= {end_ts};
    limit 50;
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
    today = datetime.now().strftime("%Y-%m-%d")

    if not games:
        return (
            f"🎮 Video Game Releases ({today})\n\n"
            "No releases found today."
        )

    message = f"🎮 Video Game Releases ({today})\n\n"

    for game in games:
        message += f"• {game['name']}\n"

        platforms = game.get("platforms", [])

        if platforms:
            platform_names = ", ".join(
                p["name"] for p in platforms
            )
            message += f"  🎯 {platform_names}\n"

        message += "\n"

    return message[:4000]


def send_telegram(text):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=30,
    )

    response.raise_for_status()


def main():
    token = get_access_token()
    games = get_games_released_today(token)

    message = build_message(games)

    send_telegram(message)


if __name__ == "__main__":
    main()
