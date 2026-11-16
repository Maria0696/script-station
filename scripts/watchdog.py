# Vigilante diario: avisa si el cron de Vercel no lanzó los workflows de
# hoy. Heimdall solo ve workflows que fallan, no los que nunca arrancan.
# Lo ejecuta el schedule de GitHub (watchdog.yml): no depende de Vercel y
# un retraso de horas no importa para un vigilante.

import logging
from datetime import UTC, datetime

from core.config import DAILY_WORKFLOWS
from core.github import get_workflow_runs
from core.logs import configure_logging
from core.notifications import notifications

logger = logging.getLogger(__name__)


def get_today():
    # En UTC, como el cron de Vercel (07:00 UTC) y las fechas de GitHub
    return datetime.now(UTC).date()


def ran_on(run, workflow_file, day):
    return run.get("path", "").endswith(f"/{workflow_file}") and run.get(
        "created_at", ""
    ).startswith(day.isoformat())


def find_missing_workflows(runs, day):
    return [
        workflow_file
        for workflow_file in DAILY_WORKFLOWS
        if not any(ran_on(run, workflow_file, day) for run in runs)
    ]


def build_missing_message(missing):
    lines = ["⏰ WORKFLOWS SIN EJECUTAR HOY", ""]

    lines.extend(DAILY_WORKFLOWS[workflow_file] for workflow_file in missing)

    lines.extend(
        [
            "",
            "El cron diario de Vercel (/api/cron) no los ha lanzado.",
            "Revisa sus logs en Vercel o lánzalos desde aquí.",
        ]
    )

    return "\n".join(lines)


def build_launch_keyboard(missing):
    return {
        "inline_keyboard": [
            [
                {
                    "text": f"▶️ Lanzar {DAILY_WORKFLOWS[workflow_file]}",
                    "callback_data": f"dispatch:{workflow_file}",
                }
            ]
            for workflow_file in missing
        ]
    }


def check_daily_workflows():
    missing = find_missing_workflows(get_workflow_runs(), get_today())

    if not missing:
        logger.info("All daily workflows ran today.")

        return []

    logger.warning("Daily workflows missing today: %s", ", ".join(missing))

    notifications.emit(
        "workflow.missed",
        build_missing_message(missing),
        reply_markup=build_launch_keyboard(missing),
    )

    return missing


def main():
    configure_logging()

    check_daily_workflows()


if __name__ == "__main__":  # pragma: no cover
    main()
