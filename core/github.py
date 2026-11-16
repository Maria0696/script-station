import base64
import json
from urllib import request
from urllib.error import HTTPError

from core.config import GITHUB_BRANCH, GITHUB_REPO, GITHUB_TOKEN, WATCHLIST_PATH


def github_request(method, path, data=None):
    # Ejecuta una llamada a GitHub
    url = f"https://api.github.com/repos/{GITHUB_REPO}/{path}"

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method=method,
    )

    # La URL siempre parte de una base https:// fija
    with request.urlopen(req, timeout=30) as response:  # noqa: S310
        content = response.read()

    if not content:
        return {}

    return json.loads(content)


def get_watchlist():
    # Lee watchlist.json desde GitHub
    result = github_request("GET", (f"contents/{WATCHLIST_PATH}?ref={GITHUB_BRANCH}"))

    content = base64.b64decode(result["content"]).decode("utf-8")

    return (json.loads(content), result["sha"])


def save_watchlist(watchlist, sha, message="chore: update game watchlist"):
    # Actualiza watchlist.json en GitHub.
    # El sha hace que GitHub rechace la escritura
    # si otro proceso cambió el archivo entretanto
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

        except HTTPError as error:
            if error.code != 409 or attempt == attempts:
                raise


def get_workflow_runs():
    # Obtiene las últimas ejecuciones de master
    result = github_request("GET", (f"actions/runs?branch={GITHUB_BRANCH}&per_page=50"))

    return result.get("workflow_runs", [])


def dispatch_workflow(workflow_file):
    # Lanza un workflow con workflow_dispatch
    return github_request(
        "POST",
        (f"actions/workflows/{workflow_file}/dispatches"),
        {"ref": GITHUB_BRANCH},
    )


def rerun_failed_workflow_run(run_id):
    # Reejecuta los jobs fallidos de un workflow
    return github_request("POST", (f"actions/runs/{run_id}/rerun-failed-jobs"))
