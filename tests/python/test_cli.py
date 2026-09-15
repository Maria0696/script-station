from station_cli import (
    PROJECT_ROOT,
    build_menu_command,
    build_parser,
    load_environment,
    main,
    run_heimdall_status,
    run_menu,
    run_notify,
    run_releases,
    run_watchlist,
)


# ============================================================
# ENTORNO
# ============================================================

def test_load_environment(
    monkeypatch,
):
    captured = []

    monkeypatch.setattr(
        "station_cli.load_dotenv",
        lambda path:
            captured.append(path),
    )

    load_environment()

    assert captured == [
        PROJECT_ROOT
        / ".env"
    ]


# ============================================================
# MENÚ
# ============================================================

def test_build_menu_command_windows(
    monkeypatch,
):
    monkeypatch.setattr(
        "station_cli.os.name",
        "nt",
    )

    assert build_menu_command() == [
        "cmd",
        "/c",
        "bundle",
        "exec",
        "rake",
        "start_tool",
    ]


def test_build_menu_command_unix(
    monkeypatch,
):
    monkeypatch.setattr(
        "station_cli.os.name",
        "posix",
    )

    assert build_menu_command() == [
        "bundle",
        "exec",
        "rake",
        "start_tool",
    ]


def test_run_menu(
    monkeypatch,
):
    captured = {}

    class FakeResult:
        returncode = 0

    monkeypatch.setattr(
        "station_cli.shutil.which",
        lambda command:
            "bundle",
    )

    monkeypatch.setattr(
        "station_cli.build_menu_command",
        lambda: [
            "bundle",
            "exec",
            "rake",
            "start_tool",
        ],
    )

    def fake_run(
        command,
        cwd=None,
        check=None,
    ):
        captured[
            "command"
        ] = command

        captured[
            "cwd"
        ] = cwd

        captured[
            "check"
        ] = check

        return FakeResult()

    monkeypatch.setattr(
        "station_cli.subprocess.run",
        fake_run,
    )

    result = run_menu()

    assert result == 0

    assert captured[
        "command"
    ] == [
        "bundle",
        "exec",
        "rake",
        "start_tool",
    ]

    assert (
        captured["cwd"]
        == PROJECT_ROOT
    )

    assert (
        captured["check"]
        is False
    )


def test_run_menu_without_bundle(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "station_cli.shutil.which",
        lambda command:
            None,
    )

    result = run_menu()

    output = (
        capsys
        .readouterr()
        .err
    )

    assert result == 1

    assert (
        "Bundler is not available"
        in output
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
        video_game_releases,
        "main",
        lambda:
            called.append(True),
    )

    result = run_releases()

    assert result == 0

    assert called == [
        True,
    ]


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
        watchlist_monitor,
        "main",
        lambda:
            called.append(True),
    )

    result = run_watchlist()

    assert result == 0

    assert called == [
        True,
    ]


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
            captured.append(args),
    )

    result = run_notify(
        "workflow-failed"
    )

    assert result == 0

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
        heimdall,
        "build_heimdall_status",
        lambda:
            "TEST STATUS",
    )

    result = (
        run_heimdall_status()
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert result == 0

    assert (
        "TEST STATUS"
        in output
    )


# ============================================================
# PARSER
# ============================================================

def test_parser_releases():
    parser = build_parser()

    result = parser.parse_args(
        [
            "releases",
        ]
    )

    assert (
        result.command
        == "releases"
    )


def test_parser_watchlist():
    parser = build_parser()

    result = parser.parse_args(
        [
            "watchlist",
        ]
    )

    assert (
        result.command
        == "watchlist"
    )


def test_parser_notify():
    parser = build_parser()

    result = parser.parse_args(
        [
            "notify",
            "workflow-failed",
        ]
    )

    assert (
        result.command
        == "notify"
    )

    assert (
        result.notify_command
        == "workflow-failed"
    )


def test_parser_heimdall_status():
    parser = build_parser()

    result = parser.parse_args(
        [
            "heimdall",
            "status",
        ]
    )

    assert (
        result.command
        == "heimdall"
    )

    assert (
        result.heimdall_command
        == "status"
    )


# ============================================================
# MAIN
# ============================================================

def test_main_defaults_to_menu(
    monkeypatch,
):
    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_menu",
        lambda:
            0,
    )

    assert main([]) == 0


def test_main_menu(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_menu",
        lambda:
            called.append(True)
            or 0,
    )

    result = main(
        [
            "menu",
        ]
    )

    assert result == 0

    assert called == [
        True,
    ]


def test_main_releases(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_releases",
        lambda:
            called.append(True)
            or 0,
    )

    result = main(
        [
            "releases",
        ]
    )

    assert result == 0

    assert called == [
        True,
    ]


def test_main_watchlist(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_watchlist",
        lambda:
            called.append(True)
            or 0,
    )

    result = main(
        [
            "watchlist",
        ]
    )

    assert result == 0

    assert called == [
        True,
    ]


def test_main_notify(
    monkeypatch,
):
    captured = []

    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_notify",
        lambda command:
            captured.append(command)
            or 0,
    )

    result = main(
        [
            "notify",
            "workflow-failed",
        ]
    )

    assert result == 0

    assert captured == [
        "workflow-failed",
    ]


def test_main_heimdall_status(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "station_cli.load_environment",
        lambda:
            None,
    )

    monkeypatch.setattr(
        "station_cli.run_heimdall_status",
        lambda:
            called.append(True)
            or 0,
    )

    result = main(
        [
            "heimdall",
            "status",
        ]
    )

    assert result == 0

    assert called == [
        True,
    ]
