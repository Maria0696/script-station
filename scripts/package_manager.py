import platform
import subprocess

import questionary

CHOCOLATEY_INSTALL_CMD = (
    '@powershell -NoProfile '
    '-ExecutionPolicy Bypass -Command '
    '"[System.Net.ServicePointManager]'
    '::SecurityProtocol = '
    '[System.Net.ServicePointManager]'
    '::SecurityProtocol -bor 3072; '
    "iex ((New-Object System.Net.WebClient)"
    ".DownloadString('"
    "https://chocolatey.org/install.ps1'))\""
)

HOMEBREW_INSTALL_CMD = (
    '/bin/bash -c "$(curl -fsSL '
    "https://raw.githubusercontent.com/"
    "Homebrew/install/HEAD/install.sh)\""
)

FLATPAK_INSTALL_CMD = (
    "sudo apt update && "
    "sudo apt install flatpak -y && "
    "sudo flatpak remote-add "
    "--if-not-exists flathub "
    "https://flathub.org/repo/"
    "flathub.flatpakrepo"
)


class PackageManager:

    def list_operating_systems(self):
        return [
            "Windows",
            "macOS",
            "Linux",
        ]

    def install_package_manager(
        self,
        operating_system,
    ):
        installers = {
            "Windows": (
                "Windows",
                "Chocolatey",
                CHOCOLATEY_INSTALL_CMD,
            ),
            "macOS": (
                "Darwin",
                "Homebrew",
                HOMEBREW_INSTALL_CMD,
            ),
            "Linux": (
                "Linux",
                "Flatpak",
                FLATPAK_INSTALL_CMD,
            ),
        }

        selected = installers.get(
            operating_system
        )

        if not selected:
            print(
                "Operating system not "
                "recognized. Unable to "
                "proceed with installation."
            )

            return 1

        (
            expected_system,
            manager_name,
            command,
        ) = selected

        if (
            platform.system()
            != expected_system
        ):
            print(
                "\nYou are not on "
                f"{operating_system}. "
                "You cannot install the "
                "package manager."
            )

            return 1

        print(
            "\nInstalling "
            f"{manager_name} on "
            f"{operating_system}..."
        )

        result = subprocess.run(
            command,
            shell=True,
            check=False,
        )

        if result.returncode != 0:
            print(
                "\nInstallation failed "
                "with exit code "
                f"{result.returncode}."
            )

            return (
                result.returncode
                or 1
            )

        print(
            "\nInstallation completed."
        )

        return 0


def main():
    manager = PackageManager()

    operating_system = (
        questionary
        .select(
            "Select your operating system:",
            choices=(
                manager
                .list_operating_systems()
            ),
        )
        .ask()
    )

    if operating_system is None:
        return 0

    confirmed = (
        questionary
        .confirm(
            (
                "Install the package "
                "manager for "
                f"{operating_system}?"
            ),
            default=False,
        )
        .ask()
    )

    if not confirmed:
        return 0

    return (
        manager
        .install_package_manager(
            operating_system
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(
        main()
    )
