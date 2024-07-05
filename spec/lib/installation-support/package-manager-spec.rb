
require './lib/installation-support/package-manager'

RSpec.describe InstallationSupport::PackageManager do
    let(:package_manager) { InstallationSupport::PackageManager.new }
    
    describe "install_package_manager" do
        context "when operating system is Windows" do
            it "installs Chocolatey" do
                allow(package_manager).to receive(:windows?).and_return(true)
                expect(package_manager).to receive(:install_chocolatey).once
                package_manager.install_package_manager("Windows")
            end
        end

        context "when operating system is macOS" do
            it "installs Homebrew" do
                allow(package_manager).to receive(:macos?).and_return(true)
                expect(package_manager).to receive(:install_homebrew).once
                package_manager.install_package_manager("macOS")
            end
        end

        context "when operating system is Linux" do
            it "installs Flatpak" do
                allow(package_manager).to receive(:linux?).and_return(true)
                expect(package_manager).to receive(:install_flatpak).once
                package_manager.install_package_manager("Linux")
            end
        end

        context "when operating system is unrecognized" do
            it "prints an error message" do
                expect { package_manager.install_package_manager("UnknownOS") }.to output(/Operating system not recognized/).to_stdout
            end
        end
    end
end
