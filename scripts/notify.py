# Aviso de workflow fallido a Heimdall, con botón de Re-run. Se ejecuta
# como último paso de cada workflow: `if: always() && failure()`.

import os
import sys

from core.notifications import notifications


def build_workflow_failure_message(workflow, repository, server_url, run_id):
    return (
        "⚠️ WORKFLOW FAILED\n\n"
        f"🔧 {workflow}\n"
        f"📦 {repository}\n\n"
        f"🔗 {server_url}/"
        f"{repository}/actions/runs/"
        f"{run_id}"
    )


def build_rerun_keyboard(run_id):
    return {
        "inline_keyboard": [[{"text": "🔄 Re-run", "callback_data": f"rerun:{run_id}"}]]
    }


def notify_workflow_failure():
    # Variables que GitHub Actions define en cada ejecución
    workflow = os.environ["GITHUB_WORKFLOW"]

    repository = os.environ["GITHUB_REPOSITORY"]

    server_url = os.environ["GITHUB_SERVER_URL"]

    run_id = os.environ["GITHUB_RUN_ID"]

    message = build_workflow_failure_message(workflow, repository, server_url, run_id)

    keyboard = build_rerun_keyboard(run_id)

    return notifications.emit("workflow.failed", message, reply_markup=keyboard)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if args != ["workflow-failed"]:
        raise SystemExit("Usage: python -m scripts.notify workflow-failed")

    notify_workflow_failure()


if __name__ == "__main__":  # pragma: no cover
    main()
