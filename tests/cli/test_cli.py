from types import SimpleNamespace

import station_cli as cli


class FakePrompt:

    def __init__(
        self,
        value,
    ):
        self.value = value

    def ask(self):
        return self.value


# ============================================================
# ENTORNO
# ============================================================

def test_load_environment(
    monkeypatch,
):
    captured = []

    monkeypatch.setattr(
        cli,
        "load_dotenv",
        lambda path:
            captured.append(
                path
            ),
    )

    cli.load_environment()

    assert captured == [
        cli.PROJECT_ROOT
        / ".env"
    ]


def test_environment_ready_missing(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv(
        "CLI_TEST_SECRET",
        raising=False,
    )

    assert (
        cli.environment_ready(
            (
                "CLI_TEST_SECRET",
            )
        )
        is False
    )

    assert (
        "CLI_TEST_SECRET"
        in capsys
        .readouterr()
        .err
    )


def test_environment_ready_success(
    monkeypatch,
):
    monkeypatch.setenv(
        "CLI_TEST_SECRET",
        "value",
    )

    assert (
        cli.environment_ready(
            (
                "CLI_TEST_SECRET",
            )
        )
        is True
    )


# ============================================================
# INTERACCIÓN
# ============================================================

def test_select_option(
    monkeypatch,
):
    monkeypatch.setattr(
        cli.questionary,
        "select",
        lambda *args, **kwargs:
            FakePrompt(
                "Selected"
            ),
    )

    assert (
        cli.select_option(
            "Choose",
            [
                "Selected",
            ],
        )
        == "Selected"
    )


def test_confirm_action(
    monkeypatch,
):
    monkeypatch.setattr(
        cli.questionary,
        "confirm",
        lambda *args, **kwargs:
            FakePrompt(
                True
            ),
    )

    assert (
        cli.confirm_action(
            "Continue?"
        )
        is True
    )


# ============================================================
# RELEASES
# ============================================================

def test_run_releases(
    monkeypatch,
):
    from scripts import (
        video_game_releases,
    )

    called = []

    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        video_game_releases,
        "main",
        lambda:
            called.append(
                True
            ),
    )

    assert (
        cli.run_releases()
        == 0
    )

    assert called == [
        True,
    ]


def test_run_releases_cancelled(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        cli,
        "confirm_action",
        lambda message:
            False,
    )

    assert (
        cli.run_releases(
            confirm=True
        )
        == 0
    )


# ============================================================
# WATCHLIST
# ============================================================

def test_run_watchlist(
    monkeypatch,
):
    from scripts import (
        watchlist_monitor,
    )

    called = []

    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        watchlist_monitor,
        "main",
        lambda:
            called.append(
                True
            ),
    )

    assert (
        cli.run_watchlist()
        == 0
    )

    assert called == [
        True,
    ]


def test_run_watchlist_cancelled(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        cli,
        "confirm_action",
        lambda message:
            False,
    )

    assert (
        cli.run_watchlist(
            confirm=True
        )
        == 0
    )


# ============================================================
# ENTORNO INCOMPLETO
# ============================================================

def test_commands_fail_without_environment(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            False,
    )

    assert (
        cli.run_releases()
        == 1
    )

    assert (
        cli.run_watchlist()
        == 1
    )

    assert (
        cli.run_heimdall_status()
        == 1
    )

    assert (
        cli.run_heimdall_failures()
        == 1
    )


# ============================================================
# NOTIFY
# ============================================================

def test_run_notify(
    monkeypatch,
):
    from scripts import notify

    captured = []

    monkeypatch.setattr(
        notify,
        "main",
        lambda args:
            captured.append(
                args
            ),
    )

    assert (
        cli.run_notify(
            "workflow-failed"
        )
        == 0
    )

    assert captured == [
        [
            "workflow-failed",
        ]
    ]


# ============================================================
# HEIMDALL
# ============================================================

def test_run_heimdall_status(
    monkeypatch,
    capsys,
):
    from core import heimdall

    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_status",
        lambda:
            "TEST STATUS",
    )

    assert (
        cli.run_heimdall_status()
        == 0
    )

    assert (
        "TEST STATUS"
        in capsys
        .readouterr()
        .out
    )


def test_run_heimdall_failures(
    monkeypatch,
    capsys,
):
    from core import heimdall

    monkeypatch.setattr(
        cli,
        "environment_ready",
        lambda required:
            True,
    )

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_failures",
        lambda:
            "TEST FAILURES",
    )

    assert (
        cli.run_heimdall_failures()
        == 0
    )

    assert (
        "TEST FAILURES"
        in capsys
        .readouterr()
        .out
    )


# ============================================================
# WRAPPERS
# ============================================================

def test_run_add_workflow(
    monkeypatch,
):
    from scripts import (
        add_workflow,
    )

    monkeypatch.setattr(
        add_workflow,
        "main",
        lambda:
            3,
    )

    assert (
        cli.run_add_workflow()
        == 3
    )


def test_run_package_manager(
    monkeypatch,
):
    from scripts import (
        package_manager,
    )

    monkeypatch.setattr(
        package_manager,
        "main",
        lambda:
            4,
    )

    assert (
        cli.run_package_manager()
        == 4
    )


# ============================================================
# MENÚS
# ============================================================

def test_git_support_menu(
    monkeypatch,
):
    choices = iter(
        [
            "Add workflow",
            "Back",
        ]
    )

    called = []

    monkeypatch.setattr(
        cli,
        "select_option",
        lambda message, options:
            next(
                choices
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_add_workflow",
        lambda:
            called.append(
                True
            ),
    )

    cli.git_support_menu()

    assert called == [
        True,
    ]


def test_installation_support_menu(
    monkeypatch,
):
    choices = iter(
        [
            "Package manager",
            "Back",
        ]
    )

    called = []

    monkeypatch.setattr(
        cli,
        "select_option",
        lambda message, options:
            next(
                choices
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_package_manager",
        lambda:
            called.append(
                True
            ),
    )

    cli.installation_support_menu()

    assert called == [
        True,
    ]


def test_video_games_menu(
    monkeypatch,
):
    choices = iter(
        [
            "Video Game Releases",
            "Watchlist Monitor",
            "Back",
        ]
    )

    called = []

    monkeypatch.setattr(
        cli,
        "select_option",
        lambda message, options:
            next(
                choices
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_releases",
        lambda confirm=False:
            called.append(
                (
                    "releases",
                    confirm,
                )
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_watchlist",
        lambda confirm=False:
            called.append(
                (
                    "watchlist",
                    confirm,
                )
            ),
    )

    cli.video_games_menu()

    assert called == [
        (
            "releases",
            True,
        ),
        (
            "watchlist",
            True,
        ),
    ]


def test_heimdall_menu(
    monkeypatch,
):
    choices = iter(
        [
            "Status",
            "Failures",
            "Back",
        ]
    )

    called = []

    monkeypatch.setattr(
        cli,
        "select_option",
        lambda message, options:
            next(
                choices
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_heimdall_status",
        lambda:
            called.append(
                "status"
            ),
    )

    monkeypatch.setattr(
        cli,
        "run_heimdall_failures",
        lambda:
            called.append(
                "failures"
            ),
    )

    cli.heimdall_menu()

    assert called == [
        "status",
        "failures",
    ]


def test_interactive_menu(
    monkeypatch,
):
    choices = iter(
        [
            "Git Support",
            "Installation Support",
            "Video Games",
            "Heimdall",
            "Exit",
        ]
    )

    called = []

    monkeypatch.setattr(
        cli,
        "select_option",
        lambda message, options:
            next(
                choices
            ),
    )

    monkeypatch.setattr(
        cli,
        "git_support_menu",
        lambda:
            called.append(
                "github"
            ),
    )

    monkeypatch.setattr(
        cli,
        "installation_support_menu",
        lambda:
            called.append(
                "install"
            ),
    )

    monkeypatch.setattr(
        cli,
        "video_games_menu",
        lambda:
            called.append(
                "games"
            ),
    )

    monkeypatch.setattr(
        cli,
        "heimdall_menu",
        lambda:
            called.append(
                "heimdall"
            ),
    )

    assert (
        cli.interactive_menu()
        == 0
    )

    assert called == [
        "github",
        "install",
        "games",
        "heimdall",
    ]


# ============================================================
# PARSER
# ============================================================

def test_parser_nested_commands():
    parser = (
        cli.build_parser()
    )

    github = parser.parse_args(
        [
            "github",
            "add-workflow",
        ]
    )

    install = parser.parse_args(
        [
            "install",
            "package-manager",
        ]
    )

    heimdall = parser.parse_args(
        [
            "heimdall",
            "failures",
        ]
    )

    assert (
        github.github_command
        == "add-workflow"
    )

    assert (
        install.install_command
        == "package-manager"
    )

    assert (
        heimdall.heimdall_command
        == "failures"
    )


# ============================================================
# DISPATCH
# ============================================================

def test_dispatch_fallback():
    called = []

    parser = SimpleNamespace(
        print_help=lambda:
            called.append(
                True
            )
    )

    parsed = SimpleNamespace(
        command="unknown"
    )

    assert (
        cli.dispatch(
            parsed,
            parser,
        )
        == 1
    )

    assert called == [
        True,
    ]


# ============================================================
# MAIN
# ============================================================

def test_main_defaults_to_menu(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        cli,
        "interactive_menu",
        lambda:
            0,
    )

    assert (
        cli.main([])
        == 0
    )


def test_main_routes_commands(
    monkeypatch,
):
    monkeypatch.setattr(
        cli,
        "load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        cli,
        "run_releases",
        lambda:
            11,
    )

    monkeypatch.setattr(
        cli,
        "run_watchlist",
        lambda:
            12,
    )

    monkeypatch.setattr(
        cli,
        "run_add_workflow",
        lambda:
            13,
    )

    monkeypatch.setattr(
        cli,
        "run_package_manager",
        lambda:
            14,
    )

    monkeypatch.setattr(
        cli,
        "run_notify",
        lambda command:
            15,
    )

    monkeypatch.setattr(
        cli,
        "run_heimdall_status",
        lambda:
            16,
    )

    monkeypatch.setattr(
        cli,
        "run_heimdall_failures",
        lambda:
            17,
    )

    assert (
        cli.main(
            [
                "releases",
            ]
        )
        == 11
    )

    assert (
        cli.main(
            [
                "watchlist",
            ]
        )
        == 12
    )

    assert (
        cli.main(
            [
                "github",
                "add-workflow",
            ]
        )
        == 13
    )

    assert (
        cli.main(
            [
                "install",
                "package-manager",
            ]
        )
        == 14
    )

    assert (
        cli.main(
            [
                "notify",
                "workflow-failed",
            ]
        )
        == 15
    )

    assert (
        cli.main(
            [
                "heimdall",
                "status",
            ]
        )
        == 16
    )

    assert (
        cli.main(
            [
                "heimdall",
                "failures",
            ]
        )
        == 17
    )


def test_main_keyboard_interrupt(
    monkeypatch,
    capsys,
):
    class InterruptingParser:

        def parse_args(
            self,
            args,
        ):
            raise KeyboardInterrupt

    monkeypatch.setattr(
        cli,
        "load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        cli,
        "build_parser",
        lambda:
            InterruptingParser(),
    )

    assert (
        cli.main([])
        == 130
    )

    assert (
        "Exiting Script Station"
        in capsys
        .readouterr()
        .out
    )
