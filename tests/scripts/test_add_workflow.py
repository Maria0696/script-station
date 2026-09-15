import base64
from types import SimpleNamespace

import pytest

from scripts import (
    add_workflow,
)


class FakeResponse:

    def __init__(
        self,
        status_code=200,
        payload=None,
    ):
        self.status_code = (
            status_code
        )

        self._payload = (
            payload
            or {}
        )

    def json(self):
        return self._payload


class FakePrompt:

    def __init__(
        self,
        value,
    ):
        self.value = value

    def ask(self):
        return self.value


class BrokenJsonResponse:

    def json(self):
        raise ValueError(
            "Invalid JSON"
        )


def configured_tool(
    tmp_path,
):
    repos = (
        tmp_path
        / "repos.txt"
    )

    repos.write_text(
        (
            "# comment\n"
            "repo-one\n"
            "\n"
            "repo-two\n"
        ),
        encoding="utf-8",
    )

    workflow = (
        tmp_path
        / "ci.yml"
    )

    workflow.write_bytes(
        b"name: CI\n"
    )

    tool = (
        add_workflow
        .AddWorkflow()
    )

    tool.org = "test-org"
    tool.github_token = "test-token"
    tool.repo_list_path = repos
    tool.workflow_template_path = (
        workflow
    )
    tool.branch_suffix = "ci"

    return tool


# ============================================================
# CONFIG
# ============================================================

def test_load_config_uses_env_token(
    monkeypatch,
    tmp_path,
):
    repos = (
        tmp_path
        / "repos.txt"
    )

    repos.write_text(
        "repo-one\n",
        encoding="utf-8",
    )

    workflow = (
        tmp_path
        / "ci.yml"
    )

    workflow.write_bytes(
        b"name: CI\n"
    )

    config = (
        tmp_path
        / "config.yml"
    )

    config.write_text(
        "\n".join(
            [
                "org: test-org",
                (
                    "github_token_env: "
                    "CUSTOM_GITHUB_TOKEN"
                ),
                (
                    "repo_list_path: "
                    f"{repos}"
                ),
                (
                    "workflow_template_path: "
                    f"{workflow}"
                ),
                "branch_suffix: ci",
                "dry_run: false",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "CUSTOM_GITHUB_TOKEN",
        "secret-token",
    )

    tool = (
        add_workflow
        .AddWorkflow()
    )

    assert (
        tool.load_config(
            str(config)
        )
        is True
    )

    assert (
        tool.github_token
        == "secret-token"
    )

    assert (
        tool.repo_list_path
        == repos
    )

    assert (
        tool.workflow_template_path
        == workflow
    )


def test_load_config_uses_direct_token(
    tmp_path,
):
    repos = (
        tmp_path
        / "repos.txt"
    )

    repos.write_text(
        "repo-one\n",
        encoding="utf-8",
    )

    workflow = (
        tmp_path
        / "ci.yml"
    )

    workflow.write_bytes(
        b"name: CI\n"
    )

    config = (
        tmp_path
        / "config.yml"
    )

    config.write_text(
        "\n".join(
            [
                "org: test-org",
                "github_token: direct-token",
                (
                    "repo_list_path: "
                    f"{repos}"
                ),
                (
                    "workflow_template_path: "
                    f"{workflow}"
                ),
                "branch_suffix: ci",
                "dry_run: false",
            ]
        ),
        encoding="utf-8",
    )

    tool = (
        add_workflow
        .AddWorkflow()
    )

    assert (
        tool.load_config(
            str(config)
        )
        is True
    )

    assert (
        tool.github_token
        == "direct-token"
    )


def test_load_config_missing_file(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    assert (
        tool.load_config(
            str(
                tmp_path
                / "missing.yml"
            )
        )
        is False
    )


def test_load_config_reports_missing_values(
    monkeypatch,
    tmp_path,
    capsys,
):
    config = (
        tmp_path
        / "config.yml"
    )

    config.write_text(
        "{}\n",
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "GITHUB_TOKEN",
        raising=False,
    )

    tool = (
        add_workflow
        .AddWorkflow()
    )

    assert (
        tool.load_config(
            str(config)
        )
        is False
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "org"
        in output
    )

    assert (
        "repo_list_path"
        in output
    )

    assert (
        "workflow_template_path"
        in output
    )

    assert (
        "branch_suffix"
        in output
    )

    assert (
        "GITHUB_TOKEN"
        in output
    )


def test_load_config_dry_run_without_token(
    monkeypatch,
    tmp_path,
):
    repos = (
        tmp_path
        / "repos.txt"
    )

    repos.write_text(
        "repo-one\n",
        encoding="utf-8",
    )

    workflow = (
        tmp_path
        / "ci.yml"
    )

    workflow.write_bytes(
        b"name: CI\n"
    )

    config = (
        tmp_path
        / "config.yml"
    )

    config.write_text(
        "\n".join(
            [
                "org: test-org",
                (
                    "repo_list_path: "
                    f"{repos}"
                ),
                (
                    "workflow_template_path: "
                    f"{workflow}"
                ),
                "branch_suffix: ci",
                "dry_run: true",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "GITHUB_TOKEN",
        raising=False,
    )

    tool = (
        add_workflow
        .AddWorkflow()
    )

    assert (
        tool.load_config(
            str(config)
        )
        is True
    )

    assert (
        tool.dry_run
        is True
    )


# ============================================================
# REPOSITORIES
# ============================================================

def test_load_repositories(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    assert (
        tool.load_repositories()
        == [
            "repo-one",
            "repo-two",
        ]
    )


# ============================================================
# FILE VALIDATION
# ============================================================

def test_validate_files(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    assert (
        tool.validate_files()
        is True
    )

    tool.repo_list_path = (
        tmp_path
        / "missing.txt"
    )

    assert (
        tool.validate_files()
        is False
    )


def test_validate_files_missing_workflow(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    tool.workflow_template_path = (
        tmp_path
        / "missing.yml"
    )

    assert (
        tool.validate_files()
        is False
    )


def test_validate_files_without_repo_path(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    tool.repo_list_path = None

    assert (
        tool.validate_files()
        is False
    )


def test_validate_files_without_workflow_path(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    tool.workflow_template_path = None

    assert (
        tool.validate_files()
        is False
    )


# ============================================================
# TOKEN
# ============================================================

def test_validate_token(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "get",
        lambda *args, **kwargs:
            FakeResponse(
                200
            ),
    )

    assert (
        tool.validate_token()
        is True
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "get",
        lambda *args, **kwargs:
            FakeResponse(
                401
            ),
    )

    assert (
        tool.validate_token()
        is False
    )


# ============================================================
# BRANCH
# ============================================================

def test_build_branch_name(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow.time,
        "time",
        lambda:
            1234567890,
    )

    monkeypatch.setattr(
        add_workflow.secrets,
        "token_hex",
        lambda size:
            "abcdef12",
    )

    assert (
        tool.build_branch_name()
        == (
            "add-workflow-ci-"
            "1234567890-abcdef12"
        )
    )


# ============================================================
# DEFAULT BRANCH / SHA
# ============================================================

def test_get_default_branch_and_sha(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    responses = iter(
        [
            FakeResponse(
                200,
                {
                    "default_branch":
                        "master",
                },
            ),
            FakeResponse(
                200,
                {
                    "object": {
                        "sha":
                            "abc123",
                    }
                },
            ),
        ]
    )

    monkeypatch.setattr(
        tool,
        "request",
        lambda *args, **kwargs:
            next(
                responses
            ),
    )

    assert (
        tool.get_default_branch(
            "repo-one"
        )
        == "master"
    )

    assert (
        tool.get_branch_sha(
            "repo-one",
            "master",
        )
        == "abc123"
    )


def test_default_branch_missing(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        tool,
        "request",
        lambda *args, **kwargs:
            FakeResponse(
                payload={}
            ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Default branch not found"
        ),
    ):
        tool.get_default_branch(
            "repo-one"
        )


def test_branch_sha_missing(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        tool,
        "request",
        lambda *args, **kwargs:
            FakeResponse(
                payload={}
            ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Default branch SHA "
            "not found"
        ),
    ):
        tool.get_branch_sha(
            "repo-one",
            "master",
        )


# ============================================================
# CREATE BRANCH
# ============================================================

def test_create_branch(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    captured = []

    monkeypatch.setattr(
        tool,
        "request",
        lambda *args, **kwargs:
            captured.append(
                (
                    args,
                    kwargs,
                )
            )
            or FakeResponse(
                201
            ),
    )

    tool.create_branch(
        "repo-one",
        "feature",
        "abc123",
    )

    args, kwargs = (
        captured[0]
    )

    assert args == (
        "POST",
        "repo-one",
        "git/refs",
    )

    assert kwargs[
        "data"
    ] == {
        "ref":
            (
                "refs/heads/"
                "feature"
            ),
        "sha":
            "abc123",
    }


# ============================================================
# WORKFLOW UPLOAD
# ============================================================

def test_upload_workflow(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    captured = []

    monkeypatch.setattr(
        tool,
        "request",
        lambda *args, **kwargs:
            captured.append(
                (
                    args,
                    kwargs,
                )
            )
            or FakeResponse(
                201
            ),
    )

    tool.upload_workflow(
        "repo-one",
        "feature",
        (
            ".github/workflows/"
            "ci.yml"
        ),
        "ci.yml",
    )

    _, kwargs = (
        captured[0]
    )

    decoded = (
        base64
        .b64decode(
            kwargs[
                "data"
            ][
                "content"
            ]
        )
        .decode(
            "utf-8"
        )
    )

    assert (
        decoded
        == "name: CI\n"
    )


# ============================================================
# PULL REQUEST
# ============================================================

def test_create_pull_request_success(
    monkeypatch,
    tmp_path,
    capsys,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(
                201,
                {
                    "html_url":
                        (
                            "https://github.com/"
                            "test/pr/1"
                        ),
                },
            ),
    )

    tool.create_pull_request(
        "repo-one",
        "feature",
        "master",
        "ci.yml",
    )

    assert (
        "PR created"
        in capsys
        .readouterr()
        .out
    )


def test_create_pull_request_exists(
    monkeypatch,
    tmp_path,
    capsys,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(
                422,
                {
                    "errors": [
                        {
                            "message":
                                (
                                    "A pull request "
                                    "already exists"
                                )
                        }
                    ]
                },
            ),
    )

    tool.create_pull_request(
        "repo-one",
        "feature",
        "master",
        "ci.yml",
    )

    assert (
        "already exists"
        in capsys
        .readouterr()
        .out
    )


def test_create_pull_request_failure(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "post",
        lambda *args, **kwargs:
            FakeResponse(
                500
            ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Failed to create "
            "pull request"
        ),
    ):
        tool.create_pull_request(
            "repo-one",
            "feature",
            "master",
            "ci.yml",
        )


# ============================================================
# GENERIC REQUEST
# ============================================================

def test_request_success(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    captured = {}

    response = FakeResponse(
        200,
        {
            "ok": True,
        },
    )

    def fake_request(
        method,
        url,
        headers=None,
        json=None,
        timeout=None,
    ):
        captured[
            "method"
        ] = method

        captured[
            "url"
        ] = url

        captured[
            "headers"
        ] = headers

        captured[
            "json"
        ] = json

        captured[
            "timeout"
        ] = timeout

        return response

    monkeypatch.setattr(
        add_workflow.requests,
        "request",
        fake_request,
    )

    result = tool.request(
        "POST",
        "repo-one",
        "contents/test.yml",
        data={
            "value": 1,
        },
    )

    assert (
        result
        is response
    )

    assert (
        captured[
            "method"
        ]
        == "POST"
    )

    assert (
        captured[
            "url"
        ]
        == (
            "https://api.github.com/"
            "repos/test-org/repo-one/"
            "contents/test.yml"
        )
    )

    assert (
        captured[
            "json"
        ]
        == {
            "value": 1,
        }
    )

    assert (
        captured[
            "timeout"
        ]
        == 30
    )


def test_request_without_path(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    captured = {}

    def fake_request(
        method,
        url,
        headers=None,
        json=None,
        timeout=None,
    ):
        captured[
            "url"
        ] = url

        return FakeResponse(
            200
        )

    monkeypatch.setattr(
        add_workflow.requests,
        "request",
        fake_request,
    )

    tool.request(
        "GET",
        "repo-one",
    )

    assert (
        captured[
            "url"
        ]
        == (
            "https://api.github.com/"
            "repos/test-org/repo-one"
        )
    )


def test_request_failure(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow.requests,
        "request",
        lambda *args, **kwargs:
            FakeResponse(
                404
            ),
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP 404",
    ):
        tool.request(
            "GET",
            "repo-one",
        )


# ============================================================
# HEADERS
# ============================================================

def test_github_headers(
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    assert (
        tool.github_headers()
        == {
            "Authorization":
                "Bearer test-token",
            "Accept":
                (
                    "application/vnd."
                    "github+json"
                ),
            "X-GitHub-Api-Version":
                "2022-11-28",
        }
    )


# ============================================================
# PROCESS REPOSITORY
# ============================================================

def test_process_repository(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    called = []

    monkeypatch.setattr(
        tool,
        "get_default_branch",
        lambda repo:
            "master",
    )

    monkeypatch.setattr(
        tool,
        "get_branch_sha",
        lambda repo, branch:
            "abc123",
    )

    monkeypatch.setattr(
        tool,
        "create_branch",
        lambda repo, branch, sha:
            called.append(
                "branch"
            ),
    )

    monkeypatch.setattr(
        tool,
        "upload_workflow",
        lambda *args:
            called.append(
                "upload"
            ),
    )

    monkeypatch.setattr(
        tool,
        "create_pull_request",
        lambda *args:
            called.append(
                "pr"
            ),
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    tool.process_repository(
        "repo-one",
        "ci.yml",
        (
            ".github/workflows/"
            "ci.yml"
        ),
        "feature",
    )

    assert called == [
        "branch",
        "upload",
        "pr",
    ]


# ============================================================
# DRY RUN
# ============================================================

def test_dry_run_output(
    tmp_path,
    capsys,
):
    tool = configured_tool(
        tmp_path
    )

    tool.dry_run_output(
        "repo-one",
        "test-branch",
        (
            ".github/workflows/"
            "ci.yml"
        ),
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "[DRY RUN] Would update "
        "test-org/repo-one"
        in output
    )

    assert (
        "test-branch"
        in output
    )

    assert (
        ".github/workflows/ci.yml"
        in output
    )

    assert (
        "open a pull request"
        in output
    )


# ============================================================
# RUN
# ============================================================

def test_run_config_cancelled(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            True,
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            None,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_config_invalid(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            True,
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            "config.yml",
    )

    monkeypatch.setattr(
        tool,
        "load_config",
        lambda path:
            False,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_manual_cancelled(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            False,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_token_failure(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            False,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_files_failure(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            False,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_config_dry_run(
    monkeypatch,
    tmp_path,
    capsys,
):
    tool = configured_tool(
        tmp_path
    )

    def fake_load_config(
        path,
    ):
        tool.dry_run = True

        return True

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            True,
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            "config.yml",
    )

    monkeypatch.setattr(
        tool,
        "load_config",
        fake_load_config,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "load_repositories",
        lambda: [
            "repo-one",
        ],
    )

    monkeypatch.setattr(
        tool,
        "build_branch_name",
        lambda:
            "test-branch",
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    assert (
        tool.run()
        == 0
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "[DRY RUN] Would update"
        in output
    )

    assert (
        "Finished processing repositories"
        in output
    )


def test_run_success(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "load_repositories",
        lambda: [
            "repo-one",
        ],
    )

    monkeypatch.setattr(
        tool,
        "build_branch_name",
        lambda:
            "test-branch",
    )

    monkeypatch.setattr(
        tool,
        "process_repository",
        lambda *args:
            None,
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    assert (
        tool.run()
        == 0
    )


def test_run_processing_failure(
    monkeypatch,
    tmp_path,
    capsys,
):
    tool = configured_tool(
        tmp_path
    )

    def fail_processing(
        *args,
    ):
        raise RuntimeError(
            "boom"
        )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "load_repositories",
        lambda: [
            "repo-one",
        ],
    )

    monkeypatch.setattr(
        tool,
        "build_branch_name",
        lambda:
            "test-branch",
    )

    monkeypatch.setattr(
        tool,
        "process_repository",
        fail_processing,
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    assert (
        tool.run()
        == 1
    )

    assert (
        "Error processing repo-one"
        in capsys
        .readouterr()
        .out
    )


def test_run_request_exception(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "load_repositories",
        lambda: [
            "repo-one",
        ],
    )

    monkeypatch.setattr(
        tool,
        "build_branch_name",
        lambda:
            "test-branch",
    )

    monkeypatch.setattr(
        tool,
        "process_repository",
        lambda *args:
            (_ for _ in ())
            .throw(
                add_workflow
                .requests
                .RequestException(
                    "network"
                )
            ),
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    assert (
        tool.run()
        == 1
    )


def test_run_value_error(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    monkeypatch.setattr(
        tool,
        "manual_input",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_token",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "validate_files",
        lambda:
            True,
    )

    monkeypatch.setattr(
        tool,
        "load_repositories",
        lambda: [
            "repo-one",
        ],
    )

    monkeypatch.setattr(
        tool,
        "build_branch_name",
        lambda:
            "test-branch",
    )

    monkeypatch.setattr(
        tool,
        "process_repository",
        lambda *args:
            (_ for _ in ())
            .throw(
                ValueError(
                    "invalid"
                )
            ),
    )

    monkeypatch.setattr(
        tool,
        "log",
        lambda message:
            None,
    )

    assert (
        tool.run()
        == 1
    )


# ============================================================
# MANUAL INPUT
# ============================================================

def test_manual_input_missing_required(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    answers = iter(
        [
            "test-org",
            None,
            "ci.yml",
            "ci",
        ]
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            next(
                answers
            ),
    )

    assert (
        tool.manual_input()
        is False
    )


def test_manual_input_dry_run(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    repos = (
        tmp_path
        / "repos.txt"
    )

    workflow = (
        tmp_path
        / "ci.yml"
    )

    answers = iter(
        [
            "test-org",
            str(repos),
            str(workflow),
            "ci",
        ]
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            next(
                answers
            ),
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            True,
    )

    assert (
        tool.manual_input()
        is True
    )

    assert (
        tool.repo_list_path
        == repos
    )

    assert (
        tool.workflow_template_path
        == workflow
    )

    assert (
        tool.dry_run
        is True
    )


def test_manual_input_reads_env_token(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    answers = iter(
        [
            "test-org",
            str(
                tmp_path
                / "repos.txt"
            ),
            str(
                tmp_path
                / "ci.yml"
            ),
            "ci",
        ]
    )

    monkeypatch.setenv(
        "GITHUB_TOKEN",
        "env-token",
    )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        lambda *args, **kwargs:
            next(
                answers
            ),
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    assert (
        tool.manual_input()
        is True
    )

    assert (
        tool.github_token
        == "env-token"
    )


def test_manual_input_prompts_for_token(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    answers = iter(
        [
            "test-org",
            str(
                tmp_path
                / "repos.txt"
            ),
            str(
                tmp_path
                / "ci.yml"
            ),
            "ci",
        ]
    )

    monkeypatch.delenv(
        "GITHUB_TOKEN",
        raising=False,
    )

    def fake_ask(
        message,
        secret=False,
    ):
        if secret:
            return (
                "prompt-token"
            )

        return next(
            answers
        )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        fake_ask,
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    assert (
        tool.manual_input()
        is True
    )

    assert (
        tool.github_token
        == "prompt-token"
    )


def test_manual_input_cancelled_token(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    answers = iter(
        [
            "test-org",
            str(
                tmp_path
                / "repos.txt"
            ),
            str(
                tmp_path
                / "ci.yml"
            ),
            "ci",
        ]
    )

    monkeypatch.delenv(
        "GITHUB_TOKEN",
        raising=False,
    )

    def fake_ask(
        message,
        secret=False,
    ):
        if secret:
            return None

        return next(
            answers
        )

    monkeypatch.setattr(
        add_workflow,
        "ask_required",
        fake_ask,
    )

    monkeypatch.setattr(
        add_workflow,
        "confirm_action",
        lambda message:
            False,
    )

    assert (
        tool.manual_input()
        is True
    )

    assert (
        tool.github_token
        == ""
    )


# ============================================================
# LOG
# ============================================================

def test_log(
    monkeypatch,
    tmp_path,
):
    tool = configured_tool(
        tmp_path
    )

    log_file = (
        tmp_path
        / "logs"
        / "add_workflow.log"
    )

    monkeypatch.setattr(
        add_workflow,
        "LOG_FILE",
        log_file,
    )

    tool.log(
        "TEST MESSAGE"
    )

    content = (
        log_file
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "TEST MESSAGE"
        in content
    )


# ============================================================
# PATHS
# ============================================================

def test_resolve_path_absolute_and_relative(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        add_workflow,
        "PROJECT_ROOT",
        tmp_path,
    )

    absolute = (
        tmp_path
        / "absolute.txt"
    )

    assert (
        add_workflow
        .resolve_path(
            absolute
        )
        == absolute
    )

    assert (
        add_workflow
        .resolve_path(
            "relative.txt"
        )
        == (
            tmp_path
            / "relative.txt"
        ).resolve()
    )


# ============================================================
# USER INPUT
# ============================================================

def test_ask_required_retries_empty_value(
    monkeypatch,
    capsys,
):
    answers = iter(
        [
            "   ",
            " value ",
        ]
    )

    monkeypatch.setattr(
        add_workflow.questionary,
        "text",
        lambda message:
            FakePrompt(
                next(
                    answers
                )
            ),
    )

    assert (
        add_workflow
        .ask_required(
            "Name"
        )
        == "value"
    )

    assert (
        "cannot be empty"
        in capsys
        .readouterr()
        .out
    )


def test_ask_required_cancelled(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow.questionary,
        "text",
        lambda message:
            FakePrompt(
                None
            ),
    )

    assert (
        add_workflow
        .ask_required(
            "Name"
        )
        is None
    )


def test_ask_required_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow.questionary,
        "password",
        lambda message:
            FakePrompt(
                " secret "
            ),
    )

    assert (
        add_workflow
        .ask_required(
            "Token",
            secret=True,
        )
        == "secret"
    )


def test_ask_required_secret_cancelled(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow.questionary,
        "password",
        lambda message:
            FakePrompt(
                None
            ),
    )

    assert (
        add_workflow
        .ask_required(
            "Token",
            secret=True,
        )
        is None
    )


def test_confirm_action(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow.questionary,
        "confirm",
        lambda *args, **kwargs:
            FakePrompt(
                True
            ),
    )

    assert (
        add_workflow
        .confirm_action(
            "Continue?"
        )
        is True
    )


def test_confirm_action_false(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow.questionary,
        "confirm",
        lambda *args, **kwargs:
            FakePrompt(
                False
            ),
    )

    assert (
        add_workflow
        .confirm_action(
            "Continue?"
        )
        is False
    )


# ============================================================
# JSON
# ============================================================

def test_safe_json():
    response = FakeResponse(
        payload={
            "ok": True,
        }
    )

    assert (
        add_workflow
        .safe_json(
            response
        )
        == {
            "ok": True,
        }
    )


def test_safe_json_invalid():
    assert (
        add_workflow
        .safe_json(
            BrokenJsonResponse()
        )
        == {}
    )


# ============================================================
# PULL REQUEST DETECTION
# ============================================================

def test_pull_request_exists():
    assert (
        add_workflow
        .pull_request_exists(
            {
                "errors": [
                    {
                        "message":
                            (
                                "A pull request "
                                "already exists"
                            )
                    }
                ]
            }
        )
    )

    assert not (
        add_workflow
        .pull_request_exists(
            {
                "errors": []
            }
        )
    )


def test_pull_request_exists_without_errors():
    assert not (
        add_workflow
        .pull_request_exists(
            {}
        )
    )


def test_pull_request_exists_other_error():
    assert not (
        add_workflow
        .pull_request_exists(
            {
                "errors": [
                    {
                        "message":
                            "Different error"
                    }
                ]
            }
        )
    )


# ============================================================
# MAIN
# ============================================================

def test_main_success(
    monkeypatch,
):
    monkeypatch.setattr(
        add_workflow,
        "AddWorkflow",
        lambda:
            SimpleNamespace(
                run=lambda:
                    7
            ),
    )

    assert (
        add_workflow.main()
        == 7
    )


def test_main_keyboard_interrupt(
    monkeypatch,
    capsys,
):
    def interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(
        add_workflow,
        "AddWorkflow",
        lambda:
            SimpleNamespace(
                run=interrupt
            ),
    )

    assert (
        add_workflow.main()
        == 130
    )

    assert (
        "Exiting Add Workflow"
        in capsys
        .readouterr()
        .out
    )
