from fastapi import FastAPI, Request

from core.heimdall import handle_heimdall_update
from core.huginn import handle_huginn_update


app = FastAPI()


# ============================================================
# INDEX
# ============================================================

@app.get("/api/index")
def index_health_check(request_data: Request):
    # Health check general
    bot = request_data.query_params.get(
        "bot",
        "huginn",
    )

    return {
        "ok": True,
        "bot": bot,
    }


@app.post("/api/index")
async def index_webhook(request_data: Request):
    # Procesa los rewrites de Vercel
    bot = request_data.query_params.get(
        "bot",
        "huginn",
    )

    update = await request_data.json()

    if bot == "heimdall":
        return handle_heimdall_update(
            update
        )

    return handle_huginn_update(
        update
    )


# ============================================================
# HUGINN
# ============================================================

@app.get("/api/telegram")
def huginn_health_check():
    # Comprueba el endpoint de Huginn
    return {
        "ok": True,
        "message": "Huginn is listening",
    }


@app.post("/api/telegram")
async def huginn_webhook(request_data: Request):
    # Recibe updates de Huginn
    update = await request_data.json()

    return handle_huginn_update(
        update
    )


# ============================================================
# HEIMDALL
# ============================================================

@app.get("/api/heimdall")
def heimdall_health_check():
    # Comprueba el endpoint de Heimdall
    return {
        "ok": True,
        "message": "Heimdall is watching",
    }


@app.post("/api/heimdall")
async def heimdall_webhook(request_data: Request):
    # Recibe updates de Heimdall
    update = await request_data.json()

    return handle_heimdall_update(
        update
    )
