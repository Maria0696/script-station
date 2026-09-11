import json
import os
from pathlib import Path
from urllib import request
from fastapi import FastAPI, Request


app = FastAPI()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])

WATCHLIST_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "watchlist.json"
)


def send_telegram_message(chat_id, text):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    data = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
        }
    ).encode("utf-8")

    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=30):
        pass


def load_watchlist():
    if not WATCHLIST_PATH.exists():
        return []

    with open(
        WATCHLIST_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_watchlist_message():
    watchlist = load_watchlist()

    if not watchlist:
        return "👀 Tu watchlist está vacía."

    lines = ["👀 MY WATCHLIST", ""]

    for game in watchlist:
        lines.append(f"• {game['name']}")

    return "\n".join(lines)


# Para comprobar el endpoint:
# https://script-station.vercel.app/api/telegram
@app.get("/api/telegram")
def health_check():
    return {
        "ok": True,
        "message": "Telegram endpoint is running",
    }


@app.post("/api/telegram")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message")

    if not isinstance(message, dict):
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = message.get("text", "").strip()

    # Solo acepta comandos de nuestro chat
    if chat_id != ALLOWED_CHAT_ID:
        return {"ok": True}

    if text == "/watchlist":
        send_telegram_message(
            chat_id,
            build_watchlist_message(),
        )

    return {"ok": True}
