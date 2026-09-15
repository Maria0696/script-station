import base64
import os
import secrets
import time
from datetime import (
    UTC,
    datetime,
)
from pathlib import Path

import questionary
import requests
import yaml

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

LOG_FILE = (
    PROJECT_ROOT
    / "logs"
    / "add_workflow.log"
)


class AddWorkflow:

    def __init__(self):
        self.org = ""
        self.github_token = ""
        self.repo_list_path = None
        self.workflow_template_path = None
        self.branch_suffix = ""
        self.dry_run = False

    def run(self):
        use_config = (
            confirm_action(
                "Do you want to use "
                "a config.yml file?"
            )
        )

        if use_config:
            config_path = (
                ask_required(
                    "Path to config.yml"
                )
            )

            if (
                not config_path
                or not self.load_config(
                    config_path
                )
            ):
                return 1

        elif not self.manual_input():
            return 1

        if (
            not self.dry_run
            and not self.validate_token()
        ):
            return 1

        if not self.validate_files():
            return 1

        repos = (
            self.load_repositories()
        )

        print(
            "\nFound "
            f"{len(repos)} repositories"
        )

        failed = False

        for index, repo in enumerate(
            repos,
            start=1,
        ):
            print(
                "\n"
                f"[{index}/{len(repos)}] "
                "Processing repo: "
                f"{self.org}/{repo}"
            )

            self.log(
                "Processing "
                f"{self.org}/{repo}"
            )

            branch_name = (
                self.build_branch_name()
            )

            workflow_filename = (
                self
                .workflow_template_path
                .name
            )

            workflow_path = (
                ".github/workflows/"
                f"{workflow_filename}"
            )

            if self.dry_run:
                self.dry_run_output(
                    repo,
                    branch_name,
                    workflow_path,
                )

                continue

            try:
                self.process_repository(
                    repo,
                    workflow_filename,
                    workflow_path,
                    branch_name,
                )

            except (
                requests.RequestException,
                RuntimeError,
                ValueError,
            ) as error:
                failed = True

                print(
                    "\nError processing "
                    f"{repo}: {error}"
                )

                self.log(
                    "ERROR "
                    f"{self.org}/{repo} - "
                    f"{error}"
                )

        print(
            "\nFinished processing "
            "repositories"
        )

        return (
            1
            if failed
            else 0
        )

    def manual_input(self):
        self.org = ask_required(
            "GitHub organization"
        )

        repo_list_path = ask_required(
            "Path to repo list file"
        )

        workflow_template_path = (
            ask_required(
                "Path to workflow template"
            )
        )

        self.branch_suffix = (
            ask_required(
                "Branch suffix"
            )
        )

        if not all(
            (
                self.org,
                repo_list_path,
                workflow_template_path,
                self.branch_suffix,
            )
        ):
            return False

        self.repo_list_path = (
            resolve_path(
                repo_list_path
            )
        )

        self.workflow_template_path = (
            resolve_path(
                workflow_template_path
            )
        )

        self.dry_run = (
            confirm_action(
                "Do you want to run "
                "in dry-run mode?"
            )
        )

        if not self.dry_run:
            self.github_token = (
                os.getenv(
                    "GITHUB_TOKEN",
                    "",
                )
                .strip()
            )

            if not self.github_token:
                self.github_token = (
                    ask_required(
                        "GitHub token",
                        secret=True,
                    )
                    or ""
                )

        return True

    def load_config(
        self,
        config_path,
    ):
        path = resolve_path(
            config_path
        )

        if not path.exists():
            print(
                "\nConfig file not found: "
                f"{path}"
            )

            return False

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            config = (
                yaml.safe_load(
                    file
                )
                or {}
            )

        self.org = str(
            config.get(
                "org",
                "",
            )
        ).strip()

        repo_list_path = str(
            config.get(
                "repo_list_path",
                "",
            )
        ).strip()

        workflow_template_path = str(
            config.get(
                "workflow_template_path",
                "",
            )
        ).strip()

        self.branch_suffix = str(
            config.get(
                "branch_suffix",
                "",
            )
        ).strip()

        self.dry_run = bool(
            config.get(
                "dry_run",
                False,
            )
        )

        token_env = str(
            config.get(
                "github_token_env",
                "GITHUB_TOKEN",
            )
        ).strip()

        self.github_token = str(
            config.get(
                "github_token",
                "",
            )
        ).strip()

        if not self.github_token:
            self.github_token = (
                os.getenv(
                    token_env,
                    "",
                )
                .strip()
            )

        if repo_list_path:
            self.repo_list_path = (
                resolve_path(
                    repo_list_path
                )
            )

        if workflow_template_path:
            self.workflow_template_path = (
                resolve_path(
                    workflow_template_path
                )
            )

        missing = []

        if not self.org:
            missing.append(
                "org"
            )

        if not repo_list_path:
            missing.append(
                "repo_list_path"
            )

        if not workflow_template_path:
            missing.append(
                "workflow_template_path"
            )

        if not self.branch_suffix:
            missing.append(
                "branch_suffix"
            )

        if (
            not self.dry_run
            and not self.github_token
        ):
            missing.append(
                token_env
            )

        if missing:
            print(
                "\nMissing configuration:"
            )

            for name in missing:
                print(
                    f"  - {name}"
                )

            return False

        print(
            "\nConfiguration loaded "
            "successfully"
        )

        return True

    def validate_token(self):
        print(
            "\nValidating GitHub token..."
        )

        response = requests.get(
            "https://api.github.com/user",
            headers=self.github_headers(),
            timeout=30,
        )

        if response.status_code == 200:
            print(
                "GitHub token validated "
                "successfully"
            )

            return True

        print(
            "Invalid GitHub token"
        )

        return False

    def validate_files(self):
        if (
            not self.repo_list_path
            or not self
            .repo_list_path
            .exists()
        ):
            print(
                "\nRepo list file not found: "
                f"{self.repo_list_path}"
            )

            return False

        if (
            not self.workflow_template_path
            or not self
            .workflow_template_path
            .exists()
        ):
            print(
                "\nWorkflow template "
                "not found: "
                f"{self.workflow_template_path}"
            )

            return False

        return True

    def load_repositories(self):
        repos = []

        lines = (
            self.repo_list_path
            .read_text(
                encoding="utf-8"
            )
            .splitlines()
        )

        for raw_line in lines:
            line = raw_line.strip()

            if (
                line
                and not line.startswith(
                    "#"
                )
            ):
                repos.append(
                    line
                )

        return repos

    def build_branch_name(self):
        return (
            "add-workflow-"
            f"{self.branch_suffix}-"
            f"{int(time.time())}-"
            f"{secrets.token_hex(4)}"
        )

    def dry_run_output(
        self,
        repo,
        branch_name,
        workflow_path,
    ):
        print(
            "[DRY RUN] Would update "
            f"{self.org}/{repo}"
        )

        print(
            "[DRY RUN] Would create "
            f"branch {branch_name}"
        )

        print(
            "[DRY RUN] Would add "
            f"{workflow_path}"
        )

        print(
            "[DRY RUN] Would commit "
            "and open a pull request"
        )

    def process_repository(
        self,
        repo,
        workflow_filename,
        workflow_path,
        branch_name,
    ):
        default_branch = (
            self.get_default_branch(
                repo
            )
        )

        base_sha = (
            self.get_branch_sha(
                repo,
                default_branch,
            )
        )

        self.create_branch(
            repo,
            branch_name,
            base_sha,
        )

        self.upload_workflow(
            repo,
            branch_name,
            workflow_path,
            workflow_filename,
        )

        self.create_pull_request(
            repo,
            branch_name,
            default_branch,
            workflow_filename,
        )

        print(
            "Finished "
            f"{self.org}/{repo}"
        )

        self.log(
            "SUCCESS "
            f"{self.org}/{repo}"
        )

    def get_default_branch(
        self,
        repo,
    ):
        response = self.request(
            "GET",
            repo,
        )

        default_branch = (
            response
            .json()
            .get(
                "default_branch"
            )
        )

        if not default_branch:
            raise RuntimeError(
                "Default branch not found"
            )

        return default_branch

    def get_branch_sha(
        self,
        repo,
        branch,
    ):
        response = self.request(
            "GET",
            repo,
            (
                "git/ref/heads/"
                f"{branch}"
            ),
        )

        sha = (
            response
            .json()
            .get(
                "object",
                {},
            )
            .get(
                "sha"
            )
        )

        if not sha:
            raise RuntimeError(
                "Default branch SHA "
                "not found"
            )

        return sha

    def create_branch(
        self,
        repo,
        branch_name,
        base_sha,
    ):
        self.request(
            "POST",
            repo,
            "git/refs",
            data={
                "ref":
                    (
                        "refs/heads/"
                        f"{branch_name}"
                    ),
                "sha":
                    base_sha,
            },
            expected=(
                201,
            ),
        )

    def upload_workflow(
        self,
        repo,
        branch_name,
        workflow_path,
        workflow_filename,
    ):
        content = (
            base64
            .b64encode(
                self
                .workflow_template_path
                .read_bytes()
            )
            .decode(
                "utf-8"
            )
        )

        self.request(
            "PUT",
            repo,
            (
                "contents/"
                f"{workflow_path}"
            ),
            data={
                "message":
                    (
                        "Add workflow "
                        f"{workflow_filename}"
                    ),
                "content":
                    content,
                "branch":
                    branch_name,
            },
            expected=(
                201,
            ),
        )

    def create_pull_request(
        self,
        repo,
        branch_name,
        default_branch,
        workflow_filename,
    ):
        response = requests.post(
            (
                "https://api.github.com/"
                "repos/"
                f"{self.org}/{repo}/pulls"
            ),
            headers=self.github_headers(),
            json={
                "title":
                    (
                        "Add workflow: "
                        f"{workflow_filename}"
                    ),
                "head":
                    branch_name,
                "base":
                    default_branch,
                "body":
                    (
                        "Add workflow "
                        f"{workflow_filename} "
                        "via automation.\n\n"
                        "Generated automatically "
                        "by script-station."
                    ),
            },
            timeout=30,
        )

        if response.status_code == 201:
            url = (
                response
                .json()
                .get(
                    "html_url"
                )
            )

            print(
                f"→ PR created: {url}"
            )

            self.log(
                f"PR CREATED {url}"
            )

            return

        body = safe_json(
            response
        )

        if pull_request_exists(
            body
        ):
            print(
                "→ Pull request "
                "already exists"
            )

            self.log(
                "PR ALREADY EXISTS "
                f"{self.org}/{repo}"
            )

            return

        raise RuntimeError(
            "Failed to create "
            "pull request: HTTP "
            f"{response.status_code}"
        )

    def request(
        self,
        method,
        repo,
        path="",
        data=None,
        expected=(200,),
    ):
        suffix = (
            f"/{path}"
            if path
            else ""
        )

        response = requests.request(
            method,
            (
                "https://api.github.com/"
                "repos/"
                f"{self.org}/{repo}"
                f"{suffix}"
            ),
            headers=self.github_headers(),
            json=data,
            timeout=30,
        )

        if (
            response.status_code
            not in expected
        ):
            raise RuntimeError(
                "GitHub API "
                f"{method} failed: HTTP "
                f"{response.status_code}"
            )

        return response

    def github_headers(self):
        return {
            "Authorization":
                (
                    "Bearer "
                    f"{self.github_token}"
                ),
            "Accept":
                (
                    "application/vnd."
                    "github+json"
                ),
            "X-GitHub-Api-Version":
                "2022-11-28",
        }

    def log(
        self,
        message,
    ):
        LOG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with LOG_FILE.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                "["
                f"{datetime.now(UTC).isoformat()}"
                "] "
                f"{message}\n"
            )


def resolve_path(
    value,
):
    path = (
        Path(
            str(value)
        )
        .expanduser()
    )

    if path.is_absolute():
        return path

    return (
        PROJECT_ROOT
        / path
    ).resolve()


def ask_required(
    message,
    secret=False,
):
    while True:
        prompt = (
            questionary.password
            if secret
            else questionary.text
        )

        answer = (
            prompt(
                f"{message}:"
            )
            .ask()
        )

        if answer is None:
            return None

        answer = answer.strip()

        if answer:
            return answer

        print(
            f"{message}: "
            "This field cannot be empty"
        )


def confirm_action(
    message,
):
    return bool(
        questionary
        .confirm(
            message,
            default=False,
        )
        .ask()
    )


def safe_json(
    response,
):
    try:
        return response.json()

    except ValueError:
        return {}


def pull_request_exists(
    body,
):
    return any(
        (
            "A pull request "
            "already exists"
        )
        in error.get(
            "message",
            "",
        )
        for error in body.get(
            "errors",
            [],
        )
    )


def main():
    try:
        return (
            AddWorkflow()
            .run()
        )

    except KeyboardInterrupt:
        print(
            "\nExiting Add Workflow."
        )

        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        main()
    )
