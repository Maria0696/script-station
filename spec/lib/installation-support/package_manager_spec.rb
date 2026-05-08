require 'spec_helper'
require './lib/installation-support/package-manager'

RSpec.describe InstallationSupport::PackageManager do
  subject(:package_manager) { described_class.new }

  describe '#list_operating_systems' do
    it 'returns supported operating systems' do
      expect(package_manager.list_operating_systems).to eq(
        %w[Windows macOS Linux]
      )
    end
  end

  describe '#install_package_manager' do
    context 'when Windows is selected' do
      before do
        allow(package_manager).to receive(:windows?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'installs Chocolatey' do
        expect(package_manager).to receive(:system)
          .with(described_class::CHOCOLATEY_INSTALL_CMD)

        package_manager.install_package_manager('Windows')
      end
    end

    context 'when macOS is selected' do
      before do
        allow(package_manager).to receive(:macos?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'installs Homebrew' do
        expect(package_manager).to receive(:system)
          .with(described_class::HOMEBREW_INSTALL_CMD)

        package_manager.install_package_manager('macOS')
      end
    end

    context 'when Linux is selected' do
      before do
        allow(package_manager).to receive(:linux?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'installs Flatpak' do
        expect(package_manager).to receive(:system)
          .with(described_class::FLATPAK_INSTALL_CMD)

        package_manager.install_package_manager('Linux')
      end
    end

    context 'when invalid operating system is selected' do
      it 'prints error message' do
        expect do
          package_manager.install_package_manager('UnknownOS')
        end.to output(
          /Operating system not recognized/
        ).to_stdout
      end
    end
  end

  describe '#install_chocolatey' do
    context 'when current OS is Windows' do
      before do
        allow(package_manager).to receive(:windows?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'runs Chocolatey install command' do
        expect(package_manager).to receive(:system)
          .with(described_class::CHOCOLATEY_INSTALL_CMD)

        package_manager.send(:install_chocolatey)
      end
    end

    context 'when current OS is not Windows' do
      before do
        allow(package_manager).to receive(:windows?)
          .and_return(false)
      end

      it 'prints OS error' do
        expect do
          package_manager.send(:install_chocolatey)
        end.to output(
          /You are not on Windows/
        ).to_stdout
      end
    end
  end

  describe '#install_homebrew' do
    context 'when current OS is macOS' do
      before do
        allow(package_manager).to receive(:macos?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'runs Homebrew install command' do
        expect(package_manager).to receive(:system)
          .with(described_class::HOMEBREW_INSTALL_CMD)

        package_manager.send(:install_homebrew)
      end
    end

    context 'when current OS is not macOS' do
      before do
        allow(package_manager).to receive(:macos?)
          .and_return(false)
      end

      it 'prints OS error' do
        expect do
          package_manager.send(:install_homebrew)
        end.to output(
          /You are not on macOS/
        ).to_stdout
      end
    end
  end

  describe '#install_flatpak' do
    context 'when current OS is Linux' do
      before do
        allow(package_manager).to receive(:linux?)
          .and_return(true)

        allow(package_manager).to receive(:system)
      end

      it 'runs Flatpak install command' do
        expect(package_manager).to receive(:system)
          .with(described_class::FLATPAK_INSTALL_CMD)

        package_manager.send(:install_flatpak)
      end
    end

    context 'when current OS is not Linux' do
      before do
        allow(package_manager).to receive(:linux?)
          .and_return(false)
      end

      it 'prints OS error' do
        expect do
          package_manager.send(:install_flatpak)
        end.to output(
          /You are not on Linux/
        ).to_stdout
      end
    end
  end

  describe '#windows?' do
    it 'detects Windows OS' do
      allow(RbConfig::CONFIG).to receive(:[])
        .with('host_os')
        .and_return('mingw')

      expect(package_manager.send(:windows?)).to be_truthy
    end
  end

  describe '#macos?' do
    it 'detects macOS' do
      allow(RbConfig::CONFIG).to receive(:[])
        .with('host_os')
        .and_return('darwin')

      expect(package_manager.send(:macos?)).to be_truthy
    end
  end

  describe '#linux?' do
    it 'detects Linux OS' do
      allow(RbConfig::CONFIG).to receive(:[])
        .with('host_os')
        .and_return('linux')

      expect(package_manager.send(:linux?)).to be_truthy
    end
  end

  describe '#print_os_error' do
    it 'prints OS mismatch error' do
      expect do
        package_manager.send(:print_os_error, 'Windows')
      end.to output(
        /You are not on Windows/
      ).to_stdout
    end
  end
end
