require './lib/installation-support/package-manager'

RSpec.describe InstallationSupport::PackageManager do
  let(:package_manager) { InstallationSupport::PackageManager.new }

  shared_examples "installs package manager" do |os, method|
    before do
      allow(package_manager).to receive("#{os.downcase}?".to_sym).and_return(true)
    end

    it "installs #{method}" do
      expect(package_manager).to receive("install_#{method}".to_sym).once
      package_manager.install_package_manager(os)
    end
  end

  describe "install_package_manager" do
    context "when operating system is Windows" do
      include_examples "installs package manager", "Windows", "chocolatey"
    end

    context "when operating system is macOS" do
      include_examples "installs package manager", "macOS", "homebrew"
    end

    context "when operating system is Linux" do
      include_examples "installs package manager", "Linux", "flatpak"
    end

    context "when operating system is unrecognized" do
      it "prints an error message" do
        expect { package_manager.install_package_manager("UnknownOS") }.to output(/Operating system not recognized/).to_stdout
      end
    end
  end
end
