import os
import sys

from core.notifications import (
    notifications,
)


def build_workflow_failure_message(
    workflow,
    repository,
    server_url,
    run_id,
):
    # Construye el mensaje común de fallo
    return (
        "⚠️ WORKFLOW FAILED\n\n"
        f"🔧 {workflow}\n"
        f"📦 {repository}\n\n"
        f"🔗 {server_url}/"
        f"{repository}/actions/runs/"
        f"{run_id}"
    )


def build_rerun_keyboard(
    run_id,
):
    # Añade el botón para reintentar el workflow
    return {
        "inline_keyboard": [
            [
                {
                    "text":
                        "🔄 Re-run",
                    "callback_data":
                        f"rerun:{run_id}",
                }
            ]
        ]
    }


def notify_workflow_failure():
    # GitHub Actions proporciona estas variables
    workflow = os.environ[
        "GITHUB_WORKFLOW"
    ]

    repository = os.environ[
        "GITHUB_REPOSITORY"
    ]

    server_url = os.environ[
        "GITHUB_SERVER_URL"
    ]

    run_id = os.environ[
        "GITHUB_RUN_ID"
    ]

    message = (
        build_workflow_failure_message(
            workflow,
            repository,
            server_url,
            run_id,
        )
    )

    keyboard = (
        build_rerun_keyboard(
            run_id
        )
    )

    return notifications.emit(
        "workflow.failed",
        message,
        reply_markup=keyboard,
    )


def main(
    args=None,
):
    # Permite añadir otros tipos de aviso en el futuro
    if args is None:
        args = sys.argv[1:]

    if args != [
        "workflow-failed"
    ]:
        raise SystemExit(
            "Usage: "
            "python -m scripts.notify "
            "workflow-failed"
        )

    notify_workflow_failure()


if __name__ == "__main__":  # pragma: no cover
    main()
