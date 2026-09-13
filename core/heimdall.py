from datetime import datetime
from zoneinfo import ZoneInfo

from core.config import (
    HEIMDALL_CHAT_ID,
    WORKFLOWS,
)

from core.github import (
    get_workflow_runs,
)

from core.telegram import (
    send_heimdall_message,
)


MADRID_TIMEZONE = ZoneInfo(
    "Europe/Madrid"
)


FAILURE_CONCLUSIONS = {
    "failure",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
}


# ============================================================
# ESTILO
# ============================================================

def build_title(
    title,
    icon="",
    indent=0,
):
    # Encabezado con posición configurable
    title_text = (
        f"{icon} {title}"
        if icon
        else title
    )

    return (
        "━━━━━━━━━━━━━━━━━━━\n"
        f"{' ' * indent}{title_text}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ============================================================
# WORKFLOWS
# ============================================================

def format_run_time(date_string):
    # Convierte la hora de GitHub a Madrid
    if not date_string:
        return "Hora desconocida"

    run_time = (
        datetime.fromisoformat(
            date_string.replace(
                "Z",
                "+00:00",
            )
        )
        .astimezone(
            MADRID_TIMEZONE
        )
    )

    now = datetime.now(
        MADRID_TIMEZONE
    )

    if (
        run_time.date()
        == now.date()
    ):
        return run_time.strftime(
            "Hoy %H:%M"
        )

    return run_time.strftime(
        "%d-%m-%Y %H:%M"
    )


def workflow_status(run):
    # Convierte el estado de GitHub a texto
    if not run:
        return "⚪ Sin datos"

    if (
        run.get("status")
        != "completed"
    ):
        return "🟡 RUNNING"

    conclusion = run.get(
        "conclusion"
    )

    if conclusion == "success":
        return "🟢 OK"

    if conclusion == "cancelled":
        return "🟠 CANCELLED"

    if conclusion == "skipped":
        return "⚪ SKIPPED"

    if conclusion == "neutral":
        return "⚪ NEUTRAL"

    return "🔴 FAILED"


def get_latest_workflows():
    # Busca la última ejecución de cada workflow
    runs = get_workflow_runs()

    latest_runs = {}

    for workflow_name in WORKFLOWS:
        latest_runs[
            workflow_name
        ] = next(
            (
                run
                for run in runs
                if (
                    run.get("name")
                    == workflow_name
                )
            ),
            None,
        )

    return latest_runs


def count_incidents(latest_runs):
    # Cuenta workflows actualmente fallidos
    return sum(
        1
        for run in latest_runs.values()
        if (
            run
            and run.get("status")
            == "completed"
            and run.get(
                "conclusion"
            )
            in FAILURE_CONCLUSIONS
        )
    )


# ============================================================
# MENSAJES
# ============================================================

def build_heimdall_status():
    # Construye el panel de estado
    latest_runs = (
        get_latest_workflows()
    )

    incidents = count_incidents(
        latest_runs
    )

    lines = [
        build_title(
            "ESTADO SCRIPT STATION",
            icon="🛡️",
            indent=12,
        ).rstrip(),
        "",
    ]

    for (
        workflow_name,
        label,
    ) in WORKFLOWS.items():

        run = latest_runs[
            workflow_name
        ]

        lines.append(
            (
                f"{label} — "
                f"{workflow_status(run)}"
            )
        )

        if run:
            lines.append(
                (
                    "      "
                    f"{format_run_time(run.get('updated_at'))}"
                )
            )

        lines.append("")

    lines.append(
        (
            "⚠️ Incidencias activas: "
            f"{incidents}"
        )
    )

    return "\n".join(
        lines
    )


def build_heimdall_help():
    # Lista de comandos de Heimdall
    return (
        build_title(
            "COMANDOS",
            icon="🛡️",
            indent=22,
        )
        + "/status\n"
        + "Estado de Script Station.\n\n"
        + "/help\n"
        + "Muestra esta ayuda."
    )


# ============================================================
# COMANDOS
# ============================================================

def handle_heimdall_message(message):
    # Procesa comandos de Heimdall
    chat_id = str(
        message
        .get("chat", {})
        .get("id", "")
    )

    text = message.get(
        "text",
        "",
    ).strip()

    if (
        chat_id
        != HEIMDALL_CHAT_ID
    ):
        return {
            "ok": True
        }

    # Estado
    if text in {
        "/start",
        "/status",
    }:
        send_heimdall_message(
            chat_id,
            build_heimdall_status(),
        )

    # Ayuda
    elif text == "/help":
        send_heimdall_message(
            chat_id,
            build_heimdall_help(),
        )

    return {
        "ok": True
    }


# ============================================================
# ENTRADA
# ============================================================

def handle_heimdall_update(update):
    # Entrada principal de Heimdall
    message = update.get(
        "message"
    )

    if not isinstance(
        message,
        dict,
    ):
        return {
            "ok": True
        }

    return handle_heimdall_message(
        message
    )
