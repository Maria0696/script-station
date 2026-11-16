import base64
import json

import requests

from core.config import GITHUB_BRANCH, GITHUB_REPO, GITHUB_TOKEN, WATCHLIST_PATH
from core.http import create_session, raise_for_status

# GET y PUT son seguros de repetir (el PUT de la watchlist lleva sha).
# Los POST lanzan o relanzan workflows: repetirlos los duplicaría
session = create_session(methods={"GET", "PUT"})


def github_request(method, path, data=None):
    response = session.request(
        method,
        f"https://api.github.com/repos/{GITHUB_REPO}/{path}",
        json=data,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )

    raise_for_status(response, "GitHub", f"{method} {path}")

    if not response.content:
        return {}

    return response.json()


def get_watchlist():
    result = github_request("GET", (f"contents/{WATCHLIST_PATH}?ref={GITHUB_BRANCH}"))

    content = base64.b64decode(result["content"]).decode("utf-8")

    return (json.loads(content), result["sha"])


def save_watchlist(watchlist, sha, message="chore: update game watchlist"):
    # Cada guardado es un commit en master. El sha es el de la versión
    # leída: si otro proceso la cambió entretanto, GitHub responde 409
    content = json.dumps(watchlist, ensure_ascii=False, indent=2) + "\n"

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    github_request(
        "PUT",
        f"contents/{WATCHLIST_PATH}",
        {
            "message": message,
            "content": encoded_content,
            "sha": sha,
            "branch": GITHUB_BRANCH,
        },
    )


def update_watchlist(change, message="chore: update game watchlist"):
    # Lee, modifica y guarda la watchlist. change(watchlist) la modifica
    # en sitio y devuelve (resultado, cambiado). Si otro proceso la
    # guardó entretanto (409), repite una vez con la versión nueva
    attempts = 2

    for attempt in range(1, attempts + 1):
        watchlist, sha = get_watchlist()

        result, changed = change(watchlist)

        if not changed:
            return result

        try:
            save_watchlist(watchlist, sha, message)

            return result

        except requests.HTTPError as error:
            conflict = error.response is not None and error.response.status_code == 409

            if not conflict or attempt == attempts:
                raise


def get_workflow_runs():
    # Las 50 más recientes bastan: Heimdall y el watchdog solo miran hoy
    result = github_request("GET", (f"actions/runs?branch={GITHUB_BRANCH}&per_page=50"))

    return result.get("workflow_runs", [])


def dispatch_workflow(workflow_file):
    return github_request(
        "POST",
        (f"actions/workflows/{workflow_file}/dispatches"),
        {"ref": GITHUB_BRANCH},
    )


def rerun_failed_workflow_run(run_id):
    return github_request("POST", (f"actions/runs/{run_id}/rerun-failed-jobs"))
