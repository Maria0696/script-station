import base64

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

    workflow.write_text(
        "name: CI\n",
        encoding="utf-8",
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

    args, kwargs = captured[0]

    assert args == (
        "POST",
        "repo-one",
        "git/refs",
    )

    assert kwargs[
        "data"
    ] == {
        "ref":
            "refs/heads/feature",
        "sha":
            "abc123",
    }


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

    _, kwargs = captured[0]

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
