#!/usr/bin/env ruby
require 'colorize'

class PackageManager
  CHOCOLATEY_INSTALL_CMD = "@powershell -NoProfile -ExecutionPolicy Bypass -Command \"[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))\""
  HOMEBREW_INSTALL_CMD = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  FLATPAK_INSTALL_CMD = "sudo apt update && sudo apt install flatpak -y && sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"

  def list_operating_systems
    ["Windows", "macOS", "Linux"]
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
      puts "\nInstalling Chocolatey on Windows..."
      system(CHOCOLATEY_INSTALL_CMD)
      puts "\nInstallation completed.".green
    else
      print_os_error("Windows")
    end
  end

  def install_homebrew
    if macos?
      puts "\nInstalling Homebrew on macOS..."
      system(HOMEBREW_INSTALL_CMD)
      puts "\nInstallation completed.".green
    else
      print_os_error("macOS")
    end
  end

  def install_flatpak
    if linux?
      puts "\nInstalling Flatpak on Linux..."
      system(FLATPAK_INSTALL_CMD)
      puts "\nInstallation completed.".green
    else
      print_os_error("Linux")
    end
  end

  def windows?
    /cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM
  end

  def macos?
    /darwin/ =~ RUBY_PLATFORM
  end

  def linux?
    /linux/ =~ RUBY_PLATFORM
  end

  def print_os_error(expected_os)
    puts "\nYou are not on #{expected_os}. You cannot install the package manager.".red
  end
end

def main
  package_manager = PackageManager.new
  os = prompt_user_for_os(package_manager.list_operating_systems)
  if os
    package_manager.install_package_manager(os)
  else
    puts "Invalid selection. Exiting.".red
  end
end

def prompt_user_for_os(os_list)
  puts "\nPlease select your operating system:"
  os_list.each_with_index do |os, index|
    puts "#{index + 1}. #{os}"
  end
  print "\nEnter the number of your choice: ".yellow
  choice = gets.chomp.to_i
  os_list[choice - 1] if choice.between?(1, os_list.length)
end

main if __FILE__ == $0
