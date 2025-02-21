require 'colorize'

module InstallationSupport
  class PackageManager
    CHOCOLATEY_INSTALL_CMD = "@powershell -NoProfile -ExecutionPolicy Bypass -Command \"[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))\""
    HOMEBREW_INSTALL_CMD = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    FLATPAK_INSTALL_CMD = "sudo apt update && sudo apt install flatpak -y && sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"

    # Function to list supported operating systems
    def list_operating_systems
      ["Windows", "macOS", "Linux"]
    end

    # Function to install the appropriate package manager based on the OS
    def install_package_manager(os)
      case os
      when "Windows"
        install_chocolatey
      when "macOS"
        install_homebrew
      when "Linux"
        install_flatpak
      else
        puts "Operating system not recognized. Unable to proceed with installation."
      end
    end

    private

    # Function to install Chocolatey on Windows
    def install_chocolatey
      if windows?
        puts "\nInstalling Chocolatey on Windows..."
        system(CHOCOLATEY_INSTALL_CMD)
        puts "\nInstallation completed.".green
      else
        print_os_error("Windows")
      end
    end

    # Function to install Homebrew on macOS
    def install_homebrew
      if macos?
        puts "\nInstalling Homebrew on macOS..."
        system(HOMEBREW_INSTALL_CMD)
        puts "\nInstallation completed.".green
      else
        print_os_error("macOS")
      end
    end

    # Function to install Flatpak on Linux
    def install_flatpak
      if linux?
        puts "\nInstalling Flatpak on Linux..."
        system(FLATPAK_INSTALL_CMD)
        puts "\nInstallation completed.".green
      else
        print_os_error("Linux")
      end
    end

    # Function to check if the operating system is Windows
    def windows?
      RbConfig::CONFIG['host_os'] =~ /mswin|msys|mingw|cygwin|bccwin|wince|emc/
    end

    # Function to check if the operating system is macOS
    def macos?
      RbConfig::CONFIG['host_os'] =~ /darwin/
    end

    # Function to check if the operating system is Linux
    def linux?
      RbConfig::CONFIG['host_os'] =~ /linux/
    end

    # Function to print an error message if the OS does not match the expected OS
    def print_os_error(expected_os)
      puts "\nYou are not on #{expected_os}. You cannot install the package manager.".red
    end
  end
end
