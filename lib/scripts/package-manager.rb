#!/usr/bin/env ruby

require 'colorize'

class PackageManager
  CHOCOLATEY_INSTALL_CMD = [
    '@powershell -NoProfile -ExecutionPolicy Bypass -Command ',
    '"[System.Net.ServicePointManager]::SecurityProtocol = ',
    '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ',
    "iex ((New-Object System.Net.WebClient).DownloadString('",
    "https://chocolatey.org/install.ps1'))\""
  ].join.freeze

  HOMEBREW_INSTALL_CMD = [
    '/bin/bash -c "$(curl -fsSL ',
    'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  ].join.freeze

  FLATPAK_INSTALL_CMD = [
    'sudo apt update && ',
    'sudo apt install flatpak -y && ',
    'sudo flatpak remote-add --if-not-exists flathub ',
    'https://flathub.org/repo/flathub.flatpakrepo'
  ].join.freeze

  def initialize
    Signal.trap('INT') do
      puts "\n\nInterrupt detected. Exiting the program...".red
      exit
    end
  end

  # Function to list supported operating systems
  def list_operating_systems
    %w[Windows macOS Linux]
  end

  # Function to install the appropriate package manager based on the OS
  def install_package_manager(os)
    case os
    when 'Windows'
      install_chocolatey
    when 'macOS'
      install_homebrew
    when 'Linux'
      install_flatpak
    else
      puts 'Operating system not recognized. Unable to proceed with installation.'
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
      print_os_error('Windows')
    end
  end

  # Function to install Homebrew on macOS
  def install_homebrew
    if macos?
      puts "\nInstalling Homebrew on macOS..."
      system(HOMEBREW_INSTALL_CMD)
      puts "\nInstallation completed.".green
    else
      print_os_error('macOS')
    end
  end

  # Function to install Flatpak on Linux
  def install_flatpak
    if linux?
      puts "\nInstalling Flatpak on Linux..."
      system(FLATPAK_INSTALL_CMD)
      puts "\nInstallation completed.".green
    else
      print_os_error('Linux')
    end
  end

  # Function to check if the operating system is Windows
  def windows?
    /cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM
  end

  # Function to check if the operating system is macOS
  def macos?
    /darwin/ =~ RUBY_PLATFORM
  end

  # Function to check if the operating system is Linux
  def linux?
    /linux/ =~ RUBY_PLATFORM
  end

  # Function to print an error message if the OS does not match the expected OS
  def print_os_error(expected_os)
    puts "\nYou are not on #{expected_os}. You cannot install the package manager.".red
  end
end

# Main function to execute the script
def main
  package_manager = PackageManager.new
  os = prompt_user_for_os(package_manager.list_operating_systems)

  if os
    package_manager.install_package_manager(os)
  else
    puts "\nInvalid selection. Exiting...".red
  end
end

# Function to prompt the user for the operating system
def prompt_user_for_os(os_list)
  puts "\nPlease select your operating system:"

  os_list.each_with_index do |os, index|
    puts "#{index + 1}. #{os}"
  end

  print "\nEnter the number of your choice: ".yellow

  choice = gets.chomp.to_i

  os_list[choice - 1] if choice.between?(1, os_list.length)
end

# Execute the main function if this file is run directly
main if __FILE__ == $PROGRAM_NAME
