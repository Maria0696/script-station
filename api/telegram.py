import json
import os
from pathlib import Path
from urllib import request
from http.server import BaseHTTPRequestHandler


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])

WATCHLIST_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "watchlist.json"
)


def send_telegram_message(chat_id, text):
    # Envía una respuesta al usuario
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
    # Lee la watchlist del repositorio
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


class handler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        # Respuesta HTTP del endpoint
        body = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.end_headers()

        self.wfile.write(body)


    def do_GET(self):
    # Para comprobar el endpoint: https://script-station.vercel.app/api/telegram

    # Comprueba que el endpoint sigue activo
    self.send_json(
        200,
        {
            "ok": True,
            "message": "Telegram endpoint is running",
        },
    )


    def do_POST(self):
        # Lee el update enviado por Telegram
        content_length = int(
            self.headers.get(
                "Content-Length",
                0,
            )
        )

        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_json(
                400,
                {
                    "ok": False,
                    "error": "Invalid JSON",
                },
            )
            return

        message = update.get("message")

        if not isinstance(message, dict):
            self.send_json(200, {"ok": True})
            return

        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        text = message.get("text", "").strip()

        # Solo acepta comandos de nuestro chat
        if chat_id != ALLOWED_CHAT_ID:
            self.send_json(200, {"ok": True})
            return

        # Comando /watchlist
        if text == "/watchlist":
            send_telegram_message(
                chat_id,
                build_watchlist_message(),
            )

        self.send_json(
            200,
            {"ok": True},
        )
