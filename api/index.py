import hmac
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import (
    CRON_SECRET,
    DAILY_WORKFLOWS,
    HEIMDALL_WEBHOOK_SECRET,
    HUGINN_WEBHOOK_SECRET,
)
from core.github import dispatch_workflow
from core.heimdall import handle_heimdall_update
from core.huginn import handle_huginn_update

# Vercel enruta /api/telegram, /api/heimdall y /api/cron a este archivo
# reescribiéndolos a /api/index?bot=... o ?cron=daily (vercel.json).
# Por eso cada ruta existe dos veces: con su nombre y vía /api/index.
app = FastAPI()

logger = logging.getLogger(__name__)

# Nombre de la cabecera, no un secreto
TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"  # noqa: S105


def secret_matches(expected, received):
    # Si falta el secreto en la configuración se rechaza todo, en vez de
    # dejar la API abierta. compare_digest evita ataques por tiempo
    if not expected or not received:
        return False

    return hmac.compare_digest(expected.encode("utf-8"), received.encode("utf-8"))


def unauthorized():
    return JSONResponse(status_code=401, content={"ok": False})


async def process_update(request_data: Request, handler, secret):
    # Telegram envía el secret_token registrado con setWebhook; sin él,
    # cualquiera con la URL podría manejar los bots
    if not secret_matches(secret, request_data.headers.get(TELEGRAM_SECRET_HEADER)):
        logger.warning("Rejected Telegram update with invalid secret")

        return unauthorized()

    # Telegram reintenta el update si no recibe un 2xx,
    # así que los errores se registran sin devolver 500
    try:
        update = await request_data.json()

        return handler(update)

    except Exception:
        logger.exception("Error processing Telegram update")

        return {"ok": True}


def run_daily_cron(request_data: Request):
    # Vercel Cron envía "Authorization: Bearer <CRON_SECRET>"
    expected = f"Bearer {CRON_SECRET}" if CRON_SECRET else None

    if not secret_matches(expected, request_data.headers.get("Authorization")):
        logger.warning("Rejected cron request with invalid secret")

        return unauthorized()

    # GitHub retrasa horas los "schedule",
    # así que el cron lanza los workflows a la hora
    for workflow_file in DAILY_WORKFLOWS:
        dispatch_workflow(workflow_file)

    return {"ok": True, "dispatched": list(DAILY_WORKFLOWS)}


@app.get("/api/index")
def index_health_check(request_data: Request):
    if request_data.query_params.get("cron") == "daily":
        return run_daily_cron(request_data)

    bot = request_data.query_params.get("bot", "huginn")

    return {"ok": True, "bot": bot}


@app.post("/api/index")
async def index_webhook(request_data: Request):
    bot = request_data.query_params.get("bot", "huginn")

    if bot == "heimdall":
        return await process_update(
            request_data, handle_heimdall_update, HEIMDALL_WEBHOOK_SECRET
        )

    return await process_update(
        request_data, handle_huginn_update, HUGINN_WEBHOOK_SECRET
    )


@app.get("/api/cron")
def daily_cron(request_data: Request):
    return run_daily_cron(request_data)


@app.get("/api/telegram")
def huginn_health_check():
    return {"ok": True, "message": "Huginn is listening"}


@app.post("/api/telegram")
async def huginn_webhook(request_data: Request):
    return await process_update(
        request_data, handle_huginn_update, HUGINN_WEBHOOK_SECRET
    )


@app.get("/api/heimdall")
def heimdall_health_check():
    return {"ok": True, "message": "Heimdall is watching"}


@app.post("/api/heimdall")
async def heimdall_webhook(request_data: Request):
    return await process_update(
        request_data, handle_heimdall_update, HEIMDALL_WEBHOOK_SECRET
    )
