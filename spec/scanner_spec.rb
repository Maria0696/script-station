require 'spec_helper'
require './lib/scanner/scanner'

RSpec.describe Scanner do
  let(:menu_path) { './spec/fixtures/menu' }

  let(:non_existent_path) do
    './spec/fixtures/does_not_exist'
  end

  let(:entry1_path) do
    File.join(menu_path, 'entry1')
  end

  let(:entry2_path) do
    File.join(menu_path, 'entry2')
  end

  describe '#scan_folder' do
    it 'returns the list of folders' do
      list_of_entries = described_class.scan_folder(menu_path)

      expect(list_of_entries).to match_array(
        %w[entry1 entry2]
      )
    end

    it 'raises an exception when directory does not exist' do
      expect do
        described_class.scan_folder(non_existent_path)
      end.to raise_error(
        RuntimeError,
        /Directory does not exists!/
      )
    end
  end

  describe '#scan_files' do
    it 'returns the list of files for entry1' do
      list_of_files = described_class.scan_files(entry1_path)

      expect(list_of_files).to match_array(
        %w[task1.rb task2.rb]
      )
    end

    it 'returns the list of files for entry2' do
      list_of_files = described_class.scan_files(entry2_path)

      expect(list_of_files).to match_array(
        %w[task1.rb]
      )
    end
  end
end