require './lib/utils/prompt'
require './lib/installation-support/package-manager'

class PackageManager
  def initialize(prompt)
    @prompt = prompt
    @package_manager = InstallationSupport::PackageManager.new
  end

  def run
    operating_systems = @package_manager.list_operating_systems

    operating_systems_selected = @prompt.select('Which operating system do you want to use?', filter: true) do |menu|
      operating_systems.each do |operating_system_name|
        menu.choice operating_system_name
      end
    end

    @package_manager.install_package_manager(operating_systems_selected)
  end
end