from fastapi.testclient import TestClient

from api import index as api_index


client = TestClient(
    api_index.app
)


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
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "update": update,
    }
