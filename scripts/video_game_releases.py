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
    fields
        name,
        total_rating,
        cover.image_id,
        platforms.name,
        first_release_date;

    where first_release_date >= {start_ts}
      & first_release_date <= {end_ts};

    sort total_rating desc;
    limit 100;
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


def classify_platform(game):
    platforms = game.get("platforms", [])

    names = [p["name"].lower() for p in platforms]

    if any("playstation" in p for p in names):
        return "🔵 PLAYSTATION"

    if any("xbox" in p for p in names):
        return "🟢 XBOX"

    if any("switch" in p or "nintendo" in p for p in names):
        return "🔴 NINTENDO"

    if any("pc" in p or "windows" in p for p in names):
        return "⚫ PC"

    return "🎲 OTHER"


def build_message(games):
    today = datetime.now().strftime("%d %b %Y")

    sections = {
        "🔵 PLAYSTATION": [],
        "🟢 XBOX": [],
        "🔴 NINTENDO": [],
        "⚫ PC": [],
        "🎲 OTHER": [],
    }

    for game in games:
        sections[classify_platform(game)].append(game)

    message = (
        "🎮━━━━━━━━━━━━━━━━━━━━━━🎮\n"
        "      <b>RELEASES TODAY</b>\n"
        f"          {today}\n"
        "🎮━━━━━━━━━━━━━━━━━━━━━━🎮\n\n"
    )

    for platform, items in sections.items():
        if not items:
            continue

        message += f"{platform}\n"
        message += "━━━━━━━━━━━━━━━\n\n"

        for game in items[:10]:
            message += f"🎯 <b>{game['name']}</b>\n"

            rating = game.get("total_rating")

            if rating:
                message += f"⭐ {round(rating)} IGDB\n"

            message += "\n"

    return message[:900]


def get_featured_cover(games):
    for game in games:
        cover = game.get("cover")

        if cover and cover.get("image_id"):
            image_id = cover["image_id"]

            return (
                f"https://images.igdb.com/igdb/image/upload/"
                f"t_cover_big/{image_id}.jpg"
            )

    return None


def send_release_message(message, cover_url):
    if cover_url:
        image = requests.get(cover_url, timeout=30)

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": message,
                "parse_mode": "HTML",
            },
            files={
                "photo": (
                    "cover.jpg",
                    image.content,
                    "image/jpeg",
                )
            },
            timeout=60,
        ).raise_for_status()

        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=30,
    ).raise_for_status()


def main():
    token = get_access_token()

    games = get_games_released_today(token)

    message = build_message(games)

    cover_url = get_featured_cover(games)

    send_release_message(message, cover_url)


if __name__ == "__main__":
    main()
