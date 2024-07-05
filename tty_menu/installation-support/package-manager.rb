
require './lib/utils/prompt'
require './lib/installation-support/package-manager'

class PackageManager
  def initialize(prompt)
    @prompt = prompt
  end

  def run
    step do
        operating_systems = InstallationSupport::PackageManager.new.list_operating_systems

        operating_systems_selected = @prompt.select('Which operating system do you want to use?', filter: true) do |operating_system|
        operating_systems.each do |operating_system_name|
            operating_system.choice operating_system_name
        end
      end

      InstallationSupport::PackageManager.new.install_package_manager(operating_systems_selected)
    end
  end
end