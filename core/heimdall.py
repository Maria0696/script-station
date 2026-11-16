# Heimdall: bot de Telegram que vigila los workflows de GitHub Actions.
# Responde a /status y /failures y gestiona los botones de los avisos:
# "🔄 Re-run" (workflow fallido) y "▶️ Lanzar" (workflow que no se ejecutó).
# Los avisos los envían los propios workflows (scripts/notify.py y
# scripts/watchdog.py); este módulo solo atiende al chat HEIMDALL_CHAT_ID.

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from core.config import DAILY_WORKFLOWS, HEIMDALL_CHAT_ID, WORKFLOWS
from core.github import dispatch_workflow, get_workflow_runs, rerun_failed_workflow_run
from core.telegram import (
    answer_heimdall_callback,
    get_update_chat_id,
    send_heimdall_message,
)

logger = logging.getLogger(__name__)

ERROR_MESSAGE = "❌ No he podido consultar GitHub. Inténtalo de nuevo en un rato."

MADRID_TIMEZONE = ZoneInfo("Europe/Madrid")


# Conclusiones de GitHub que cuentan como incidencia. "cancelled" y
# "skipped" no: suelen ser intencionadas
FAILURE_CONCLUSIONS = {
    "failure",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
}


def build_title(title, icon="", indent=0):
    title_text = f"{icon} {title}" if icon else title

    return f"━━━━━━━━━━━━━━━━━━━\n{' ' * indent}{title_text}\n━━━━━━━━━━━━━━━━━━━\n\n"


# ============================================================
# WORKFLOWS
# ============================================================


def format_run_time(date_string):
    if not date_string:
        return "Hora desconocida"

    run_time = datetime.fromisoformat(date_string).astimezone(MADRID_TIMEZONE)

    now = datetime.now(MADRID_TIMEZONE)

    if run_time.date() == now.date():
        return run_time.strftime("Hoy %H:%M")

    return run_time.strftime("%d-%m-%Y %H:%M")


def workflow_status(run):
    if not run:
        return "⚪ Sin datos"

    if run.get("status") != "completed":
        return "🟡 RUNNING"

    conclusion = run.get("conclusion")

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
    runs = get_workflow_runs()

    latest_runs = {}

    for workflow_name in WORKFLOWS:
        latest_runs[workflow_name] = next(
            (run for run in runs if (run.get("name") == workflow_name)), None
        )

    return latest_runs


def count_incidents(latest_runs):
    return sum(
        1
        for run in latest_runs.values()
        if (
            run
            and run.get("status") == "completed"
            and run.get("conclusion") in FAILURE_CONCLUSIONS
        )
    )


def get_failed_workflows():
    latest_runs = get_latest_workflows()

    return {
        workflow_name: run
        for workflow_name, run in latest_runs.items()
        if (
            run
            and run.get("status") == "completed"
            and run.get("conclusion") in FAILURE_CONCLUSIONS
        )
    }


# ============================================================
# MENSAJES
# ============================================================


def build_heimdall_status():
    latest_runs = get_latest_workflows()

    incidents = count_incidents(latest_runs)

    lines = [build_title("ESTADO SCRIPT STATION", icon="🛡️", indent=12).rstrip(), ""]

    for workflow_name, label in WORKFLOWS.items():
        run = latest_runs[workflow_name]

        lines.append(f"{label} — {workflow_status(run)}")

        if run:
            lines.append(f"      {format_run_time(run.get('updated_at'))}")

        lines.append("")

    lines.append(f"⚠️ Incidencias activas: {incidents}")

    return "\n".join(lines)


def build_heimdall_failures(failed_workflows=None):
    if failed_workflows is None:
        failed_workflows = get_failed_workflows()

    lines = [build_title("FALLOS ACTIVOS", icon="🛡️", indent=18).rstrip(), ""]

    if not failed_workflows:
        lines.append("✅ No hay fallos activos.")

        return "\n".join(lines)

    for workflow_name, run in failed_workflows.items():
        label = WORKFLOWS[workflow_name]

        lines.append(f"🔴 {label}")

        branch = run.get("head_branch", "Desconocida")

        lines.append(f"      🌿 {branch}")

        lines.append(f"      🕒 {format_run_time(run.get('updated_at'))}")

        url = run.get("html_url")

        if url:
            lines.append(f"      🔗 {url}")

        lines.append("")

    lines.append(f"⚠️ Total: {len(failed_workflows)}")

    return "\n".join(lines)


def build_heimdall_help():
    return (
        build_title("COMANDOS", icon="🛡️", indent=22)
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


def build_failures_keyboard(failed_workflows):
    buttons = []

    for workflow_name, run in failed_workflows.items():
        run_id = run.get("id")

        if not run_id:
            continue

        label = WORKFLOWS[workflow_name]

        buttons.append(
            [{"text": f"🔄 Re-run {label}", "callback_data": f"rerun:{run_id}"}]
        )

    if not buttons:
        return None

    return {"inline_keyboard": buttons}


# ============================================================
# CALLBACKS
# ============================================================


def handle_heimdall_callback(callback):
    callback_id = callback.get("id")

    callback_data = callback.get("data", "")

    message = callback.get("message", {})

    chat_id = str(message.get("chat", {}).get("id", ""))

    # Bot de un solo usuario: otros chats se ignoran sin responder
    if chat_id != HEIMDALL_CHAT_ID:
        return {"ok": True}

    # Relanza solo los jobs que fallaron, no el workflow entero
    if callback_data.startswith("rerun:"):
        try:
            run_id = int(callback_data.split(":", 1)[1])

            rerun_failed_workflow_run(run_id)

        except (ValueError, OSError):
            if callback_id:
                answer_heimdall_callback(
                    callback_id, ("❌ No se pudo iniciar el Re-run")
                )

            return {"ok": True}

        if callback_id:
            answer_heimdall_callback(callback_id, "🔄 Re-run solicitado")

        send_heimdall_message(chat_id, (f"🔄 Re-run solicitado.\n\n🆔 Run #{run_id}"))

    # Lanzar un workflow diario que no se ejecutó (aviso del watchdog)
    elif callback_data.startswith("dispatch:"):
        handle_dispatch_callback(chat_id, callback_id, callback_data)

    return {"ok": True}


def handle_dispatch_callback(chat_id, callback_id, callback_data):
    # Solo se lanzan los workflows diarios conocidos: el callback_data
    # viene de Telegram y no debe poder lanzar cualquier workflow
    workflow_file = callback_data.split(":", 1)[1]

    label = DAILY_WORKFLOWS.get(workflow_file)

    if not label:
        if callback_id:
            answer_heimdall_callback(callback_id, "❌ Workflow desconocido")

        return

    try:
        dispatch_workflow(workflow_file)

    except OSError:
        if callback_id:
            answer_heimdall_callback(callback_id, "❌ No se pudo lanzar")

        return

    if callback_id:
        answer_heimdall_callback(callback_id, "▶️ Lanzado")

    send_heimdall_message(chat_id, f"▶️ Lanzado: {label}")


# ============================================================
# COMANDOS
# ============================================================


def handle_heimdall_message(message):
    chat_id = str(message.get("chat", {}).get("id", ""))

    text = message.get("text", "").strip()

    if chat_id != HEIMDALL_CHAT_ID:
        return {"ok": True}

    if text in {"/start", "/status"}:
        send_heimdall_message(chat_id, build_heimdall_status())

    elif text == "/failures":
        failed_workflows = get_failed_workflows()

        send_heimdall_message(
            chat_id,
            build_heimdall_failures(failed_workflows),
            build_failures_keyboard(failed_workflows),
        )

    elif text == "/help":
        send_heimdall_message(chat_id, build_heimdall_help())

    return {"ok": True}


# ============================================================
# ENTRADA
# ============================================================


def dispatch_heimdall_update(update):
    callback = update.get("callback_query")

    if isinstance(callback, dict):
        return handle_heimdall_callback(callback)

    message = update.get("message")

    if isinstance(message, dict):
        return handle_heimdall_message(message)

    return {"ok": True}


def report_heimdall_error(update):
    chat_id = get_update_chat_id(update)

    if chat_id != HEIMDALL_CHAT_ID:
        return

    try:
        send_heimdall_message(chat_id, ERROR_MESSAGE)

    except Exception:
        logger.exception("Could not send the Heimdall error message")


def handle_heimdall_update(update):
    # Un fallo (GitHub caído) se registra y se avisa en el chat;
    # a Telegram se le responde OK para que no reenvíe el mismo update
    try:
        return dispatch_heimdall_update(update)

    except Exception:
        logger.exception("Heimdall could not process an update")

        report_heimdall_error(update)

        return {"ok": True}
