from fastapi import FastAPI, Request
from core.heimdall import handle_heimdall_update
from core.huginn import handle_huginn_update


app = FastAPI()


@app.get("/api/index")
def health_check(request_data: Request):
    # Comprueba que Script Station está funcionando
    bot = request_data.query_params.get("bot", "huginn")

    return {
        "ok": True,
        "bot": bot,
    }


@app.post("/api/index")
async def telegram_webhook(request_data: Request):
    # Envía cada update al bot correspondiente
    bot = request_data.query_params.get("bot", "huginn")
    update = await request_data.json()

    if bot == "heimdall":
        return handle_heimdall_update(update)

    return handle_huginn_update(update)
