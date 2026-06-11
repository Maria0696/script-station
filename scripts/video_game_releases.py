import os
from collections import defaultdict
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


def platform_group(platform_name):
    platform_name = platform_name.lower()

    if "switch" in platform_name or "nintendo" in platform_name:
        return "🔴 Nintendo"

    if "playstation" in platform_name or "ps5" in platform_name:
        return "🔵 PlayStation"

    if "xbox" in platform_name:
        return "🟢 Xbox"

    if (
        "pc" in platform_name
        or "windows" in platform_name
        or "steam" in platform_name
    ):
        return "💻 PC"

    return None


def build_message(games):
    today = datetime.now().strftime("%Y-%m-%d")

    if not games:
        return (
            f"🎮 Video Game Releases ({today})\n\n"
            "No releases found today."
        )

    grouped_games = defaultdict(set)

    for game in games:
        game_name = game["name"]

        for platform in game.get("platforms", []):
            group = platform_group(platform["name"])

            if group:
                grouped_games[group].add(game_name)

    order = [
        "🔴 Nintendo",
        "🔵 PlayStation",
        "🟢 Xbox",
        "💻 PC",
    ]

    message = f"🎮 Video Game Releases ({today})\n\n"

    found = False

    for section in order:
        if section not in grouped_games:
            continue

        found = True

        message += f"{section}\n"

        for game_name in sorted(grouped_games[section]):
            message += f"• {game_name}\n"

        message += "\n"

    if not found:
        message += "No major platform releases found."

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
