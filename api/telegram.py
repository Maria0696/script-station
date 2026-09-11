import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        # Respuesta JSON estándar
        body = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(body)


    def do_GET(self):
        # Permite comprobar que el endpoint está activo
        self.send_json(
            200,
            {
                "ok": True,
                "message": "Telegram endpoint is running"
            }
        )


    def do_POST(self):
        # Lee el JSON enviado por Telegram
        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_json(
                400,
                {"ok": False, "error": "Invalid JSON"}
            )
            return

        # Temporal: muestra el update en los logs
        print("Telegram update:")
        print(update)

        # Telegram necesita recibir un 2XX
        self.send_json(
            200,
            {"ok": True}
        )
