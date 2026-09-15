import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
)


def load_environment():
    # Carga las variables locales del proyecto
    load_dotenv(
        PROJECT_ROOT
        / ".env"
    )


def build_menu_command():
    # En Windows los ejecutables de Ruby
    # suelen resolverse mediante cmd.
    if os.name == "nt":
        return [
            "cmd",
            "/c",
            "bundle",
            "exec",
            "rake",
            "start_tool",
        ]

    return [
        "bundle",
        "exec",
        "rake",
        "start_tool",
    ]


def run_menu():
    # Mantiene exactamente el menú Ruby actual
    bundle = shutil.which(
        "bundle"
    )

    if bundle is None:
        print(
            "Bundler is not available. "
            "Install the Ruby dependencies "
            "before opening the menu.",
            file=sys.stderr,
        )

        return 1

    result = subprocess.run(
        build_menu_command(),
        cwd=PROJECT_ROOT,
        check=False,
    )

    return result.returncode


def run_releases():
    # Ejecuta Daily Video Game Releases
    from scripts import (  # noqa: PLC0415
        video_game_releases,
    )

    video_game_releases.main()

    return 0


def run_watchlist():
    # Ejecuta Watchlist Release Monitor
    from scripts import (  # noqa: PLC0415
        watchlist_monitor,
    )

    watchlist_monitor.main()

    return 0


def run_notify(
    command,
):
    # Reutiliza el CLI de notificaciones
    from scripts import notify  # noqa: PLC0415

    notify.main(
        [
            command,
        ]
    )

    return 0


def run_heimdall_status():
    # Reutiliza el panel existente de Heimdall
    from core.heimdall import (  # noqa: PLC0415
        build_heimdall_status,
    )

    print(
        build_heimdall_status()
    )

    return 0


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

    return parser


def main(
    args=None,
):
    # Carga .env antes de importar
    # módulos que dependen de configuración.
    load_environment()

    parser = build_parser()

    parsed = parser.parse_args(
        args
    )

    # Sin argumentos mantiene el
    # comportamiento de rake start_tool.
    if (
        parsed.command is None
        or parsed.command == "menu"
    ):
        return run_menu()

    if (
        parsed.command
        == "releases"
    ):
        return run_releases()

    if (
        parsed.command
        == "watchlist"
    ):
        return run_watchlist()

    if (
        parsed.command
        == "notify"
    ):
        return run_notify(
            parsed.notify_command
        )

    if (
        parsed.command
        == "heimdall"
        and parsed.heimdall_command
        == "status"
    ):
        return (
            run_heimdall_status()
        )

    parser.print_help()

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        main()
    )
