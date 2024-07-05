
module InstallationSupport
  class PackageManager
    def list_operating_systems
        operating_systems = ["Windows", "macOS", "Linux"]
        operating_systems
    end

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

    def install_chocolatey
        if windows?
            puts "Installing Chocolatey on Windows..."
            
            system("@powershell -NoProfile -ExecutionPolicy Bypass -Command \"[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))\"")
            
            puts
            puts "Installation completed."
        else
            puts "You are not on Windows. You cannot install Chocolatey."
        end
    end
      
    def install_homebrew
        if macos?
            puts "Installing Homebrew on macOS..."

            system('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

            puts
            puts "Installation completed."
        else
            puts "You are not on macOS. You cannot install Homebrew."
        end
    end
      
    def install_flatpak
        if linux?
            puts "Installing Flatpak on Linux..."

            system("sudo apt update && sudo apt install flatpak -y")
            system("sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo")

            puts
            puts "Installation completed."
        else
            puts "You are not on Linux. You cannot install Flatpak."
        end
    end
      
    def windows?
        RbConfig::CONFIG['host_os'] =~ /mswin|msys|mingw|cygwin|bccwin|wince|emc/
    end
      
    def macos?
        RbConfig::CONFIG['host_os'] =~ /darwin/
    end
      
    def linux?
        RbConfig::CONFIG['host_os'] =~ /linux/
    end      
  end
end
  