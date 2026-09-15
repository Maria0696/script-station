from types import SimpleNamespace

from scripts import (
    package_manager,
)


class FakePrompt:

    def __init__(
        self,
        value,
    ):
        self.value = value

    def ask(self):
        return self.value


# ============================================================
# PACKAGE MANAGER
# ============================================================

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


# ============================================================
# MAIN
# ============================================================

def test_main_cancelled_selection(
    monkeypatch,
):
    monkeypatch.setattr(
        package_manager.questionary,
        "select",
        lambda *args, **kwargs:
            FakePrompt(
                None
            ),
    )

    assert (
        package_manager.main()
        == 0
    )


def test_main_not_confirmed(
    monkeypatch,
):
    monkeypatch.setattr(
        package_manager.questionary,
        "select",
        lambda *args, **kwargs:
            FakePrompt(
                "Windows"
            ),
    )

    monkeypatch.setattr(
        package_manager.questionary,
        "confirm",
        lambda *args, **kwargs:
            FakePrompt(
                False
            ),
    )

    assert (
        package_manager.main()
        == 0
    )


def test_main_installs(
    monkeypatch,
):
    monkeypatch.setattr(
        package_manager.questionary,
        "select",
        lambda *args, **kwargs:
            FakePrompt(
                "Linux"
            ),
    )

    monkeypatch.setattr(
        package_manager.questionary,
        "confirm",
        lambda *args, **kwargs:
            FakePrompt(
                True
            ),
    )

    monkeypatch.setattr(
        package_manager.PackageManager,
        "install_package_manager",
        lambda self, operating_system:
            7,
    )

    assert (
        package_manager.main()
        == 7
    )
