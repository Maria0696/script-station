from types import SimpleNamespace

from scripts import (
    package_manager,
)


def test_list_operating_systems():
    manager = (
        package_manager
        .PackageManager()
    )

    assert (
        manager
        .list_operating_systems()
        == [
            "Windows",
            "macOS",
            "Linux",
        ]
    )


def test_install_package_manager_windows(
    monkeypatch,
):
    manager = (
        package_manager
        .PackageManager()
    )

    captured = []

    monkeypatch.setattr(
        package_manager.platform,
        "system",
        lambda:
            "Windows",
    )

    monkeypatch.setattr(
        package_manager.subprocess,
        "run",
        lambda command, shell, check:
            captured.append(
                (
                    command,
                    shell,
                    check,
                )
            )
            or SimpleNamespace(
                returncode=0
            ),
    )

    assert (
        manager
        .install_package_manager(
            "Windows"
        )
        == 0
    )

    assert captured == [
        (
            package_manager
            .CHOCOLATEY_INSTALL_CMD,
            True,
            False,
        )
    ]


def test_install_package_manager_macos(
    monkeypatch,
):
    manager = (
        package_manager
        .PackageManager()
    )

    monkeypatch.setattr(
        package_manager.platform,
        "system",
        lambda:
            "Darwin",
    )

    monkeypatch.setattr(
        package_manager.subprocess,
        "run",
        lambda *args, **kwargs:
            SimpleNamespace(
                returncode=0
            ),
    )

    assert (
        manager
        .install_package_manager(
            "macOS"
        )
        == 0
    )


def test_install_package_manager_linux(
    monkeypatch,
):
    manager = (
        package_manager
        .PackageManager()
    )

    monkeypatch.setattr(
        package_manager.platform,
        "system",
        lambda:
            "Linux",
    )

    monkeypatch.setattr(
        package_manager.subprocess,
        "run",
        lambda *args, **kwargs:
            SimpleNamespace(
                returncode=0
            ),
    )

    assert (
        manager
        .install_package_manager(
            "Linux"
        )
        == 0
    )


def test_install_package_manager_wrong_os(
    monkeypatch,
    capsys,
):
    manager = (
        package_manager
        .PackageManager()
    )

    monkeypatch.setattr(
        package_manager.platform,
        "system",
        lambda:
            "Linux",
    )

    assert (
        manager
        .install_package_manager(
            "Windows"
        )
        == 1
    )

    assert (
        "You are not on Windows"
        in capsys
        .readouterr()
        .out
    )


def test_install_package_manager_unknown(
    capsys,
):
    manager = (
        package_manager
        .PackageManager()
    )

    assert (
        manager
        .install_package_manager(
            "Unknown"
        )
        == 1
    )

    assert (
        "Operating system not recognized"
        in capsys
        .readouterr()
        .out
    )


def test_install_package_manager_failure(
    monkeypatch,
):
    manager = (
        package_manager
        .PackageManager()
    )

    monkeypatch.setattr(
        package_manager.platform,
        "system",
        lambda:
            "Linux",
    )

    monkeypatch.setattr(
        package_manager.subprocess,
        "run",
        lambda *args, **kwargs:
            SimpleNamespace(
                returncode=9
            ),
    )

    assert (
        manager
        .install_package_manager(
            "Linux"
        )
        == 9
    )
