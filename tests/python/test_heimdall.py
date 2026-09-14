from datetime import datetime

from core import heimdall


# ============================================================
# ESTILO
# ============================================================

def test_build_title_with_icon():
    # Construye título con icono e indentación
    result = heimdall.build_title(
        "TEST",
        icon="🛡️",
        indent=2,
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        "  🛡️ TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


def test_build_title_without_icon():
    # Construye título sin icono
    result = heimdall.build_title(
        "TEST",
        indent=1,
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        " TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ============================================================
# FECHAS
# ============================================================

def test_format_run_time_without_date():
    # Muestra texto si no hay fecha
    assert (
        heimdall.format_run_time(None)
        == "Hora desconocida"
    )


def test_format_run_time_today(
    monkeypatch,
):
    # Formatea ejecuciones del día actual
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(
                2026,
                9,
                14,
                15,
                0,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        heimdall,
        "datetime",
        FakeDatetime,
    )

    result = heimdall.format_run_time(
        "2026-09-14T10:30:00Z"
    )

    assert result == "Hoy 12:30"


def test_format_run_time_previous_day(
    monkeypatch,
):
    # Formatea ejecuciones de otro día
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(
                2026,
                9,
                14,
                15,
                0,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        heimdall,
        "datetime",
        FakeDatetime,
    )

    result = heimdall.format_run_time(
        "2026-09-13T10:30:00Z"
    )

    assert result == "13-09-2026 12:30"


# ============================================================
# ESTADOS
# ============================================================

def test_workflow_status_without_run():
    # Detecta workflows sin datos
    assert (
        heimdall.workflow_status(None)
        == "⚪ Sin datos"
    )


def test_workflow_status_running():
    # Detecta workflow en ejecución
    run = {
        "status": "in_progress",
    }

    assert (
        heimdall.workflow_status(run)
        == "🟡 RUNNING"
    )


def test_workflow_status_success():
    # Detecta workflow correcto
    run = {
        "status": "completed",
        "conclusion": "success",
    }

    assert (
        heimdall.workflow_status(run)
        == "🟢 OK"
    )


def test_workflow_status_cancelled():
    # Detecta workflow cancelado
    run = {
        "status": "completed",
        "conclusion": "cancelled",
    }

    assert (
        heimdall.workflow_status(run)
        == "🟠 CANCELLED"
    )


def test_workflow_status_skipped():
    # Detecta workflow omitido
    run = {
        "status": "completed",
        "conclusion": "skipped",
    }

    assert (
        heimdall.workflow_status(run)
        == "⚪ SKIPPED"
    )


def test_workflow_status_neutral():
    # Detecta workflow neutral
    run = {
        "status": "completed",
        "conclusion": "neutral",
    }

    assert (
        heimdall.workflow_status(run)
        == "⚪ NEUTRAL"
    )


def test_workflow_status_failed():
    # Detecta cualquier fallo restante
    run = {
        "status": "completed",
        "conclusion": "failure",
    }

    assert (
        heimdall.workflow_status(run)
        == "🔴 FAILED"
    )


# ============================================================
# WORKFLOWS
# ============================================================

def test_get_latest_workflows(
    monkeypatch,
):
    # Obtiene la última ejecución de cada workflow
    runs = [
        {
            "name":
                "Daily Video Game Releases",
            "id": 1,
        },
        {
            "name":
                "Daily Video Game Releases",
            "id": 2,
        },
        {
            "name":
                "Quality Checks",
            "id": 3,
        },
    ]

    monkeypatch.setattr(
        heimdall,
        "get_workflow_runs",
        lambda: runs,
    )

    result = (
        heimdall.get_latest_workflows()
    )

    assert result[
        "Daily Video Game Releases"
    ]["id"] == 1

    assert result[
        "Quality Checks"
    ]["id"] == 3

    assert (
        result[
            "Watchlist Release Monitor"
        ]
        is None
    )


def test_count_incidents():
    # Cuenta solo fallos activos
    latest_runs = {
        "success": {
            "status": "completed",
            "conclusion": "success",
        },
        "failure": {
            "status": "completed",
            "conclusion": "failure",
        },
        "timeout": {
            "status": "completed",
            "conclusion": "timed_out",
        },
        "running": {
            "status": "in_progress",
            "conclusion": None,
        },
        "missing": None,
    }

    result = heimdall.count_incidents(
        latest_runs
    )

    assert result == 2


def test_count_all_failure_conclusions():
    # Reconoce todas las conclusiones de fallo
    latest_runs = {
        conclusion: {
            "status": "completed",
            "conclusion": conclusion,
        }
        for conclusion
        in heimdall.FAILURE_CONCLUSIONS
    }

    result = heimdall.count_incidents(
        latest_runs
    )

    assert result == len(
        heimdall.FAILURE_CONCLUSIONS
    )


# ============================================================
# MENSAJES
# ============================================================

def test_build_heimdall_status(
    monkeypatch,
):
    # Construye el panel completo de estado
    latest_runs = {
        "Daily Video Game Releases": {
            "status": "completed",
            "conclusion": "success",
            "updated_at":
                "2026-09-14T10:00:00Z",
        },
        "Watchlist Release Monitor": {
            "status": "completed",
            "conclusion": "failure",
            "updated_at":
                "2026-09-14T11:00:00Z",
        },
        "Quality Checks": None,
    }

    monkeypatch.setattr(
        heimdall,
        "get_latest_workflows",
        lambda: latest_runs,
    )

    monkeypatch.setattr(
        heimdall,
        "format_run_time",
        lambda date: "Hoy 12:00",
    )

    result = (
        heimdall.build_heimdall_status()
    )

    assert "🛡️ ESTADO SCRIPT STATION" in result

    assert (
        "🎮 Daily Releases — 🟢 OK"
        in result
    )

    assert (
        "👀 Watchlist Monitor — 🔴 FAILED"
        in result
    )

    assert (
        "🧪 Quality Checks — ⚪ Sin datos"
        in result
    )

    assert (
        "⚠️ Incidencias activas: 1"
        in result
    )

    assert result.count(
        "Hoy 12:00"
    ) == 2


def test_build_heimdall_help():
    # Construye el mensaje de ayuda
    result = (
        heimdall.build_heimdall_help()
    )

    assert "🛡️ COMANDOS" in result
    assert "/status" in result

    assert (
        "Estado de Script Station."
        in result
    )

    assert "/help" in result
    assert "Muestra esta ayuda." in result


# ============================================================
# COMANDOS
# ============================================================

def test_handle_heimdall_message_ignores_other_chat(
    monkeypatch,
):
    # Ignora mensajes de chats no autorizados
    sent = []

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args: sent.append(args),
    )

    result = (
        heimdall.handle_heimdall_message(
            {
                "chat": {
                    "id": "999999",
                },
                "text": "/status",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == []


def test_handle_heimdall_status(
    monkeypatch,
):
    # Responde al comando /status
    sent = []

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_status",
        lambda: "STATUS",
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda chat_id, message:
            sent.append(
                (
                    chat_id,
                    message,
                )
            ),
    )

    result = (
        heimdall.handle_heimdall_message(
            {
                "chat": {
                    "id":
                        heimdall.HEIMDALL_CHAT_ID,
                },
                "text": "  /status  ",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            heimdall.HEIMDALL_CHAT_ID,
            "STATUS",
        )
    ]


def test_handle_heimdall_start(
    monkeypatch,
):
    # /start muestra también el estado
    sent = []

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_status",
        lambda: "STATUS",
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda chat_id, message:
            sent.append(message),
    )

    heimdall.handle_heimdall_message(
        {
            "chat": {
                "id":
                    heimdall.HEIMDALL_CHAT_ID,
            },
            "text": "/start",
        }
    )

    assert sent == [
        "STATUS",
    ]


def test_handle_heimdall_help(
    monkeypatch,
):
    # Responde al comando /help
    sent = []

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_help",
        lambda: "HELP",
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda chat_id, message:
            sent.append(message),
    )

    result = (
        heimdall.handle_heimdall_message(
            {
                "chat": {
                    "id":
                        heimdall.HEIMDALL_CHAT_ID,
                },
                "text": "/help",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        "HELP",
    ]


def test_handle_heimdall_unknown_command(
    monkeypatch,
):
    # Ignora comandos desconocidos
    sent = []

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args: sent.append(args),
    )

    result = (
        heimdall.handle_heimdall_message(
            {
                "chat": {
                    "id":
                        heimdall.HEIMDALL_CHAT_ID,
                },
                "text": "/unknown",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == []


# ============================================================
# ENTRADA
# ============================================================

def test_handle_heimdall_update_without_message():
    # Ignora updates sin mensaje
    result = (
        heimdall.handle_heimdall_update(
            {}
        )
    )

    assert result == {
        "ok": True,
    }


def test_handle_heimdall_update_with_invalid_message():
    # Ignora mensajes con formato incorrecto
    result = (
        heimdall.handle_heimdall_update(
            {
                "message": "invalid",
            }
        )
    )

    assert result == {
        "ok": True,
    }


def test_handle_heimdall_update_routes_message(
    monkeypatch,
):
    # Envía mensajes válidos al handler
    message = {
        "chat": {
            "id": "123",
        },
        "text": "/status",
    }

    captured = {}

    def fake_handler(received):
        captured["message"] = received

        return {
            "ok": True,
            "handled": True,
        }

    monkeypatch.setattr(
        heimdall,
        "handle_heimdall_message",
        fake_handler,
    )

    result = (
        heimdall.handle_heimdall_update(
            {
                "message": message,
            }
        )
    )

    assert captured["message"] == message

    assert result == {
        "ok": True,
        "handled": True,
    }
