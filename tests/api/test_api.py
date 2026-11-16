from fastapi.testclient import TestClient

from api import index as api_index

client = TestClient(
    api_index.app
)

HUGINN_HEADERS = {
    "X-Telegram-Bot-Api-Secret-Token":
        "test-huginn-secret",
}

HEIMDALL_HEADERS = {
    "X-Telegram-Bot-Api-Secret-Token":
        "test-heimdall-secret",
}


# ============================================================
# INDEX
# ============================================================

def test_index_health_check_defaults_to_huginn():
    # Usa Huginn por defecto
    response = client.get(
        "/api/index"
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "bot": "huginn",
    }


def test_index_health_check_heimdall():
    # Reconoce Heimdall por query param
    response = client.get(
        "/api/index?bot=heimdall"
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "bot": "heimdall",
    }


def test_index_webhook_routes_to_huginn(
    monkeypatch,
):
    # Envía updates a Huginn por defecto
    update = {
        "message": {
            "text": "/help",
        }
    }

    monkeypatch.setattr(
        api_index,
        "handle_huginn_update",
        lambda received: {
            "bot": "huginn",
            "update": received,
        },
    )

    response = client.post(
        "/api/index",
        json=update,
        headers=HUGINN_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "bot": "huginn",
        "update": update,
    }


def test_index_webhook_routes_to_heimdall(
    monkeypatch,
):
    # Envía updates a Heimdall si se indica
    update = {
        "message": {
            "text": "/status",
        }
    }

    monkeypatch.setattr(
        api_index,
        "handle_heimdall_update",
        lambda received: {
            "bot": "heimdall",
            "update": received,
        },
    )

    response = client.post(
        "/api/index?bot=heimdall",
        json=update,
        headers=HEIMDALL_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "bot": "heimdall",
        "update": update,
    }


# ============================================================
# HUGINN
# ============================================================

def test_huginn_health_check():
    # Comprueba que Huginn está disponible
    response = client.get(
        "/api/telegram"
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "message": "Huginn is listening",
    }


def test_huginn_webhook(
    monkeypatch,
):
    # Envía el update al handler de Huginn
    update = {
        "message": {
            "text": "/watchlist",
        }
    }

    monkeypatch.setattr(
        api_index,
        "handle_huginn_update",
        lambda received: {
            "ok": True,
            "update": received,
        },
    )

    response = client.post(
        "/api/telegram",
        json=update,
        headers=HUGINN_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "update": update,
    }


# ============================================================
# HEIMDALL
# ============================================================

def test_heimdall_health_check():
    # Comprueba que Heimdall está disponible
    response = client.get(
        "/api/heimdall"
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "message": "Heimdall is watching",
    }


def test_heimdall_webhook(
    monkeypatch,
):
    # Envía el update al handler de Heimdall
    update = {
        "message": {
            "text": "/status",
        }
    }

    monkeypatch.setattr(
        api_index,
        "handle_heimdall_update",
        lambda received: {
            "ok": True,
            "update": received,
        },
    )

    response = client.post(
        "/api/heimdall",
        json=update,
        headers=HEIMDALL_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "update": update,
    }


# ============================================================
# ERRORES
# ============================================================

def test_webhook_error_returns_ok(
    monkeypatch,
    caplog,
):
    # Un fallo interno no debe provocar reintentos de Telegram
    def failing_handler(received):
        raise OSError(
            "GitHub unavailable"
        )

    monkeypatch.setattr(
        api_index,
        "handle_huginn_update",
        failing_handler,
    )

    response = client.post(
        "/api/telegram",
        json={
            "message": {
                "text": "/watchlist",
            }
        },
        headers=HUGINN_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
    }

    assert (
        "Error processing Telegram update"
        in caplog.text
    )


def test_webhook_invalid_json_returns_ok():
    # Un cuerpo no válido tampoco devuelve 500
    response = client.post(
        "/api/heimdall",
        content=b"not json",
        headers={
            **HEIMDALL_HEADERS,
            "Content-Type":
                "application/json",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
    }


# ============================================================
# AUTENTICACIÓN DE WEBHOOKS
# ============================================================

def test_webhook_rejects_missing_secret(
    monkeypatch,
):
    # Sin la cabecera de Telegram no se procesa nada
    called = []

    monkeypatch.setattr(
        api_index,
        "handle_huginn_update",
        called.append,
    )

    response = client.post(
        "/api/telegram",
        json={
            "message": {
                "text": "/unwatch",
            }
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "ok": False,
    }

    assert called == []


def test_webhook_rejects_other_bot_secret(
    monkeypatch,
):
    # El secreto de Huginn no sirve para Heimdall
    called = []

    monkeypatch.setattr(
        api_index,
        "handle_heimdall_update",
        called.append,
    )

    response = client.post(
        "/api/index?bot=heimdall",
        json={
            "message": {
                "text": "/status",
            }
        },
        headers=HUGINN_HEADERS,
    )

    assert response.status_code == 401

    assert called == []


def test_webhook_rejects_when_secret_not_configured(
    monkeypatch,
):
    # Si falta la variable de entorno se rechaza todo
    monkeypatch.setattr(
        api_index,
        "HUGINN_WEBHOOK_SECRET",
        None,
    )

    response = client.post(
        "/api/telegram",
        json={},
        headers=HUGINN_HEADERS,
    )

    assert response.status_code == 401


# ============================================================
# CRON
# ============================================================

CRON_HEADERS = {
    "Authorization":
        "Bearer test-cron-secret",
}


def test_cron_dispatches_daily_workflows(
    monkeypatch,
):
    dispatched = []

    monkeypatch.setattr(
        api_index,
        "dispatch_workflow",
        dispatched.append,
    )

    response = client.get(
        "/api/cron",
        headers=CRON_HEADERS,
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "dispatched": [
            "videogames.yml",
            "watchlist.yml",
        ],
    }

    assert dispatched == [
        "videogames.yml",
        "watchlist.yml",
    ]


def test_cron_through_index_rewrite(
    monkeypatch,
):
    # Vercel reescribe /api/cron a /api/index?cron=daily
    dispatched = []

    monkeypatch.setattr(
        api_index,
        "dispatch_workflow",
        dispatched.append,
    )

    response = client.get(
        "/api/index?cron=daily",
        headers=CRON_HEADERS,
    )

    assert response.status_code == 200

    assert len(dispatched) == 2


def test_cron_rejects_invalid_secret(
    monkeypatch,
):
    dispatched = []

    monkeypatch.setattr(
        api_index,
        "dispatch_workflow",
        dispatched.append,
    )

    for headers in (
        {},
        {
            "Authorization":
                "Bearer wrong",
        },
        {
            # Sin el prefijo "Bearer "
            "Authorization":
                "test-cron-secret",
        },
    ):
        response = client.get(
            "/api/cron",
            headers=headers,
        )

        assert response.status_code == 401

    assert dispatched == []


def test_cron_rejects_when_secret_not_configured(
    monkeypatch,
):
    monkeypatch.setattr(
        api_index,
        "CRON_SECRET",
        None,
    )

    response = client.get(
        "/api/cron",
        headers={
            "Authorization":
                "Bearer None",
        },
    )

    assert response.status_code == 401
