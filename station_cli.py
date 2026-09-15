import argparse
import os
import sys
from pathlib import Path

import questionary
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

RELEASES_ENV = (
    "IGDB_CLIENT_ID",
    "IGDB_CLIENT_SECRET",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)

WATCHLIST_ENV = RELEASES_ENV

HEIMDALL_ENV = (
    "GITHUB_TOKEN",
)


def load_environment():
    load_dotenv(
        PROJECT_ROOT
        / ".env"
    )


def missing_environment(
    required,
):
    return [
        name
        for name in required
        if not os.getenv(name)
    ]


def environment_ready(
    required,
):
    missing = (
        missing_environment(
            required
        )
    )

    if not missing:
        return True

    print(
        "\nMissing environment variables:",
        file=sys.stderr,
    )

    for name in missing:
        print(
            f"  - {name}",
            file=sys.stderr,
        )

    return False


def select_option(
    message,
    choices,
):
    return (
        questionary
        .select(
            message,
            choices=choices,
        )
        .ask()
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


def print_banner():
    print(
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "         SCRIPT STATION\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )


def run_releases(
    confirm=False,
):
    if not environment_ready(
        RELEASES_ENV
    ):
        return 1

    if (
        confirm
        and not confirm_action(
            "This will send today's "
            "releases to Telegram. Continue?"
        )
    ):
        return 0

    from scripts import (
        video_game_releases,
    )

    video_game_releases.main()

    return 0


def run_watchlist(
    confirm=False,
):
    if not environment_ready(
        WATCHLIST_ENV
    ):
        return 1

    if (
        confirm
        and not confirm_action(
            "Check the watchlist for "
            "release changes?"
        )
    ):
        return 0

    from scripts import (
        watchlist_monitor,
    )

    watchlist_monitor.main()

    return 0


def run_notify(
    command,
):
    from scripts import notify

    notify.main(
        [
            command,
        ]
    )

    return 0


def run_heimdall_status():
    if not environment_ready(
        HEIMDALL_ENV
    ):
        return 1

    from core.heimdall import (
        build_heimdall_status,
    )

    print(
        build_heimdall_status()
    )

    return 0


def run_heimdall_failures():
    if not environment_ready(
        HEIMDALL_ENV
    ):
        return 1

    from core.heimdall import (
        build_heimdall_failures,
    )

    print(
        build_heimdall_failures()
    )

    return 0


def run_add_workflow():
    from scripts.add_workflow import (
        main as add_workflow_main,
    )

    return add_workflow_main()


def run_package_manager():
    from scripts.package_manager import (
        main as package_manager_main,
    )

    return package_manager_main()


def git_support_menu():
    while True:
        choice = select_option(
            "Git Support",
            [
                "Add workflow",
                "Back",
            ],
        )

        if choice in {
            None,
            "Back",
        }:
            return

        if choice == "Add workflow":
            run_add_workflow()


def installation_support_menu():
    while True:
        choice = select_option(
            "Installation Support",
            [
                "Package manager",
                "Back",
            ],
        )

        if choice in {
            None,
            "Back",
        }:
            return

        if (
            choice
            == "Package manager"
        ):
            run_package_manager()


def video_games_menu():
    while True:
        choice = select_option(
            "Video Games",
            [
                "Video Game Releases",
                "Watchlist Monitor",
                "Back",
            ],
        )

        if choice in {
            None,
            "Back",
        }:
            return

        if (
            choice
            == "Video Game Releases"
        ):
            run_releases(
                confirm=True
            )

        elif (
            choice
            == "Watchlist Monitor"
        ):
            run_watchlist(
                confirm=True
            )


def heimdall_menu():
    while True:
        choice = select_option(
            "Heimdall",
            [
                "Status",
                "Failures",
                "Back",
            ],
        )

        if choice in {
            None,
            "Back",
        }:
            return

        if choice == "Status":
            run_heimdall_status()

        elif choice == "Failures":
            run_heimdall_failures()


def interactive_menu():
    print_banner()

    while True:
        choice = select_option(
            (
                "Which type of operation "
                "do you want to perform?"
            ),
            [
                "Git Support",
                "Installation Support",
                "Video Games",
                "Heimdall",
                "Exit",
            ],
        )

        if choice in {
            None,
            "Exit",
        }:
            print(
                "\nExiting Script Station."
            )

            return 0

        if choice == "Git Support":
            git_support_menu()

        elif (
            choice
            == "Installation Support"
        ):
            installation_support_menu()

        elif choice == "Video Games":
            video_games_menu()

        elif choice == "Heimdall":
            heimdall_menu()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="script-station",
        description=(
            "Script Station command-line "
            "interface"
        ),
    )

    subcommands = (
        parser.add_subparsers(
            dest="command",
            title="commands",
            metavar="<command>",
        )
    )

    subcommands.add_parser(
        "menu",
        help=(
            "Open the interactive "
            "Script Station menu"
        ),
    )

    subcommands.add_parser(
        "releases",
        help=(
            "Send today's video game "
            "release report"
        ),
    )

    subcommands.add_parser(
        "watchlist",
        help=(
            "Check the watchlist for "
            "release changes"
        ),
    )

    github_parser = (
        subcommands.add_parser(
            "github",
            help=(
                "Use GitHub automation "
                "tools"
            ),
        )
    )

    github_commands = (
        github_parser
        .add_subparsers(
            dest="github_command",
            required=True,
            title="commands",
            metavar="<command>",
        )
    )

    github_commands.add_parser(
        "add-workflow",
        help=(
            "Add a workflow to multiple "
            "repositories"
        ),
    )

    install_parser = (
        subcommands.add_parser(
            "install",
            help=(
                "Use installation support "
                "tools"
            ),
        )
    )

    install_commands = (
        install_parser
        .add_subparsers(
            dest="install_command",
            required=True,
            title="commands",
            metavar="<command>",
        )
    )

    install_commands.add_parser(
        "package-manager",
        help=(
            "Install a supported package "
            "manager"
        ),
    )

    notify_parser = (
        subcommands.add_parser(
            "notify",
            help=(
                "Send Script Station "
                "notifications"
            ),
        )
    )

    notify_commands = (
        notify_parser
        .add_subparsers(
            dest="notify_command",
            required=True,
            title="commands",
            metavar="<command>",
        )
    )

    notify_commands.add_parser(
        "workflow-failed",
        help=(
            "Emit a workflow.failed "
            "notification"
        ),
    )

    heimdall_parser = (
        subcommands.add_parser(
            "heimdall",
            help=(
                "Use Heimdall monitoring "
                "commands"
            ),
        )
    )

    heimdall_commands = (
        heimdall_parser
        .add_subparsers(
            dest="heimdall_command",
            required=True,
            title="commands",
            metavar="<command>",
        )
    )

    heimdall_commands.add_parser(
        "status",
        help=(
            "Show the current workflow "
            "status"
        ),
    )

    heimdall_commands.add_parser(
        "failures",
        help=(
            "Show active workflow "
            "failures"
        ),
    )

    return parser


def dispatch(
    parsed,
    parser,
):
    if parsed.command in {
        None,
        "menu",
    }:
        return interactive_menu()

    if parsed.command == "releases":
        return run_releases()

    if parsed.command == "watchlist":
        return run_watchlist()

    if (
        parsed.command == "github"
        and parsed.github_command
        == "add-workflow"
    ):
        return run_add_workflow()

    if (
        parsed.command == "install"
        and parsed.install_command
        == "package-manager"
    ):
        return run_package_manager()

    if parsed.command == "notify":
        return run_notify(
            parsed.notify_command
        )

    if (
        parsed.command == "heimdall"
        and parsed.heimdall_command
        == "status"
    ):
        return run_heimdall_status()

    if (
        parsed.command == "heimdall"
        and parsed.heimdall_command
        == "failures"
    ):
        return run_heimdall_failures()

    parser.print_help()

    return 1


def main(
    args=None,
):
    load_environment()

    parser = build_parser()

    try:
        parsed = parser.parse_args(
            args
        )

        return dispatch(
            parsed,
            parser,
        )

    except KeyboardInterrupt:
        print(
            "\nExiting Script Station."
        )

        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        main()
    )
