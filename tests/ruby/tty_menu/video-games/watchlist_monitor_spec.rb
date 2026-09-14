require 'spec_helper'
require './tty_menu/video-games/watchlist_monitor'

RSpec.describe WatchlistMonitor do
  subject(:tool) do
    described_class.new(prompt)
  end

  let(:prompt) { double('prompt') }

  around do |example|
    original_env = described_class::REQUIRED_ENV.to_h do |variable|
      [variable, ENV[variable]]
    end

    described_class::REQUIRED_ENV.each do |variable|
      ENV[variable] = 'test-value'
    end

    example.run
  ensure
    original_env.each do |variable, value|
      if value.nil?
        ENV.delete(variable)
      else
        ENV[variable] = value
      end
    end
  end

  describe '#run' do
    it 'stops when required environment variables are missing' do
      described_class::REQUIRED_ENV.each do |variable|
        ENV.delete(variable)
      end

      expect(prompt).not_to receive(:yes?)

      expect do
        tool.run
      end.to output(
        /Missing environment variables/
      ).to_stdout
    end

    it 'stops when execution is not confirmed' do
      expect(prompt).to receive(:yes?).with(
        'Check the watchlist for release changes?'
      ).and_return(false)

      expect(tool).not_to receive(:system)

      tool.run
    end

    it 'runs the script with py on Windows' do
      allow(Gem).to receive(
        :win_platform?
      ).and_return(true)

      expect(prompt).to receive(
        :yes?
      ).and_return(true)

      expect(tool).to receive(:system).with(
        'py',
        'scripts/watchlist_monitor.py'
      ).and_return(true)

      tool.run
    end

    it 'runs the script with python3 outside Windows' do
      allow(Gem).to receive(
        :win_platform?
      ).and_return(false)

      expect(prompt).to receive(
        :yes?
      ).and_return(true)

      expect(tool).to receive(:system).with(
        'python3',
        'scripts/watchlist_monitor.py'
      ).and_return(true)

      tool.run
    end

    it 'raises an error when the Python script fails' do
      allow(Gem).to receive(
        :win_platform?
      ).and_return(true)

      expect(prompt).to receive(
        :yes?
      ).and_return(true)

      expect(tool).to receive(:system).with(
        'py',
        'scripts/watchlist_monitor.py'
      ).and_return(false)

      expect do
        tool.run
      end.to raise_error(
        RuntimeError,
        'Python script failed: scripts/watchlist_monitor.py'
      )
    end
  end
end
