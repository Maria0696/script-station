import base64
import json
from urllib import request

from core.config import (
    GITHUB_BRANCH,
    GITHUB_REPO,
    GITHUB_TOKEN,
    WATCHLIST_PATH,
)


def github_request(
    method,
    path,
    data=None,
):
    # Ejecuta una llamada a GitHub
    url = (
        "https://api.github.com/repos/"
        f"{GITHUB_REPO}/{path}"
    )

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

    with request.urlopen(req, timeout=30) as response:
        content = response.read()

    if not content:
        return {}

    return json.loads(content)


def get_watchlist():
    # Lee watchlist.json desde GitHub
    result = github_request(
        "GET",
        (
            f"contents/{WATCHLIST_PATH}"
            f"?ref={GITHUB_BRANCH}"
        ),
    )

    content = base64.b64decode(
        result["content"]
    ).decode("utf-8")

    return (
        json.loads(content),
        result["sha"],
    )


def save_watchlist(watchlist, sha):
    # Actualiza watchlist.json en GitHub
    content = json.dumps(
        watchlist,
        ensure_ascii=False,
        indent=2,
    )

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    github_request(
        "PUT",
        f"contents/{WATCHLIST_PATH}",
        {
            "message": "chore: update game watchlist",
            "content": encoded_content,
            "sha": sha,
            "branch": GITHUB_BRANCH,
        },
    )


def get_workflow_runs():
    # Obtiene las últimas ejecuciones de master
    result = github_request(
        "GET",
        (
            "actions/runs"
            f"?branch={GITHUB_BRANCH}"
            "&per_page=50"
        ),
    )

    return result.get(
        "workflow_runs",
        [],
    )
