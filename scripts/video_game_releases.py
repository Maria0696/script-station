import os
from html import escape
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
    fields
        name,
        first_release_date,
        platforms.name;

    where first_release_date >= {start_ts}
      & first_release_date <= {end_ts};

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


def normalize_platform(platform_name):
    name = platform_name.lower()

    if "playstation" in name:
        return "🔵 PS5"

    if "xbox" in name:
        return "🟢 Xbox"

    if "switch" in name or "nintendo" in name:
        return "🔴 Switch"

    if "windows" in name or "pc" in name:
        return "💻 PC"

    if "mac" in name:
        return "🍎 Mac"

    if "linux" in name:
        return "🐧 Linux"

    return None


def build_message(games):
    today = datetime.now().strftime("%Y-%m-%d")

    if not games:
        return (
            f"🎮 <b>Video Game Releases ({today})</b>\n\n"
            "No releases found today."
        )

    message = f"🎮 <b>Video Game Releases ({today})</b>\n\n"

    for game in games:
        game_name = escape(game["name"])

        platforms = []

        for platform in game.get("platforms", []):
            normalized = normalize_platform(platform["name"])

            if normalized and normalized not in platforms:
                platforms.append(normalized)

        message += f"🎮 <b>{game_name}</b>\n"

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

    # útil para depurar futuros errores
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
