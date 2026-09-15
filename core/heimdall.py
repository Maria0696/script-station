from datetime import datetime
from zoneinfo import ZoneInfo

from core.config import (
    HEIMDALL_CHAT_ID,
    WORKFLOWS,
)
from core.github import (
    get_workflow_runs,
    rerun_failed_workflow_run,
)
from core.telegram import (
    answer_heimdall_callback,
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
            date_string
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


def count_incidents(
    latest_runs,
):
    # Cuenta workflows actualmente fallidos
    return sum(
        1
        for run
        in latest_runs.values()
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


def get_failed_workflows():
    # Obtiene los workflows actualmente fallidos
    latest_runs = (
        get_latest_workflows()
    )

    return {
        workflow_name: run
        for workflow_name, run
        in latest_runs.items()
        if (
            run
            and run.get("status")
            == "completed"
            and run.get(
                "conclusion"
            )
            in FAILURE_CONCLUSIONS
        )
    }


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
            f"{label} — "
            f"{workflow_status(run)}"
        )

        if run:
            lines.append(
                "      "
                f"{format_run_time(run.get('updated_at'))}"
            )

        lines.append("")

    lines.append(
        "⚠️ Incidencias activas: "
        f"{incidents}"
    )

    return "\n".join(
        lines
    )


def build_heimdall_failures(
    failed_workflows=None,
):
    # Construye el listado de fallos activos
    if failed_workflows is None:
        failed_workflows = (
            get_failed_workflows()
        )

    lines = [
        build_title(
            "FALLOS ACTIVOS",
            icon="🛡️",
            indent=18,
        ).rstrip(),
        "",
    ]

    if not failed_workflows:
        lines.append(
            "✅ No hay fallos activos."
        )

        return "\n".join(
            lines
        )

    for (
        workflow_name,
        run,
    ) in failed_workflows.items():

        label = WORKFLOWS[
            workflow_name
        ]

        lines.append(
            f"🔴 {label}"
        )

        branch = run.get(
            "head_branch",
            "Desconocida",
        )

        lines.append(
            f"      🌿 {branch}"
        )

        lines.append(
            "      🕒 "
            f"{format_run_time(run.get('updated_at'))}"
        )

        url = run.get(
            "html_url"
        )

        if url:
            lines.append(
                f"      🔗 {url}"
            )

        lines.append("")

    lines.append(
        "⚠️ Total: "
        f"{len(failed_workflows)}"
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
        + "/failures\n"
        + "Muestra los fallos activos.\n\n"
        + "/help\n"
        + "Muestra esta ayuda."
    )


# ============================================================
# BOTONES
# ============================================================

def build_failures_keyboard(
    failed_workflows,
):
    # Botones para reejecutar workflows fallidos
    buttons = []

    for (
        workflow_name,
        run,
    ) in failed_workflows.items():

        run_id = run.get(
            "id"
        )

        if not run_id:
            continue

        label = WORKFLOWS[
            workflow_name
        ]

        buttons.append(
            [
                {
                    "text":
                        f"🔄 Re-run {label}",
                    "callback_data":
                        f"rerun:{run_id}",
                }
            ]
        )

    if not buttons:
        return None

    return {
        "inline_keyboard":
            buttons
    }


# ============================================================
# CALLBACKS
# ============================================================

def handle_heimdall_callback(
    callback,
):
    # Procesa botones de Heimdall
    callback_id = callback.get(
        "id"
    )

    callback_data = callback.get(
        "data",
        "",
    )

    message = callback.get(
        "message",
        {},
    )

    chat_id = str(
        message
        .get("chat", {})
        .get("id", "")
    )

    if (
        chat_id
        != HEIMDALL_CHAT_ID
    ):
        return {
            "ok": True
        }

    # Re-run de jobs fallidos
    if callback_data.startswith(
        "rerun:"
    ):
        try:
            run_id = int(
                callback_data.split(
                    ":",
                    1,
                )[1]
            )

            rerun_failed_workflow_run(
                run_id
            )

        except (
            ValueError,
            OSError,
        ):
            if callback_id:
                answer_heimdall_callback(
                    callback_id,
                    (
                        "❌ No se pudo iniciar "
                        "el Re-run"
                    ),
                )

            return {
                "ok": True
            }

        if callback_id:
            answer_heimdall_callback(
                callback_id,
                "🔄 Re-run solicitado",
            )

        send_heimdall_message(
            chat_id,
            (
                "🔄 Re-run solicitado.\n\n"
                f"🆔 Run #{run_id}"
            ),
        )

    return {
        "ok": True
    }


# ============================================================
# COMANDOS
# ============================================================

def handle_heimdall_message(
    message,
):
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

    # Fallos activos
    elif text == "/failures":
        failed_workflows = (
            get_failed_workflows()
        )

        send_heimdall_message(
            chat_id,
            build_heimdall_failures(
                failed_workflows
            ),
            build_failures_keyboard(
                failed_workflows
            ),
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

def handle_heimdall_update(
    update,
):
    # Entrada principal de Heimdall
    callback = update.get(
        "callback_query"
    )

    if isinstance(
        callback,
        dict,
    ):
        return handle_heimdall_callback(
            callback
        )

    message = update.get(
        "message"
    )

    if isinstance(
        message,
        dict,
    ):
        return handle_heimdall_message(
            message
        )

    return {
        "ok": True
    }
