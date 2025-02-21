require './lib/scanner/scanner'

RSpec.describe 'TTY Menu Support Tasks' do
  let(:menu_path) { './spec/fixtures/menu' }
  let(:non_existent_path) { 'does_not_exist' }
  let(:entry1_path) { File.join(menu_path, 'entry1') }
  let(:entry2_path) { File.join(menu_path, 'entry2') }

  describe 'retrieving list of tty menu folders' do
    it 'returns the list of folders' do
      list_of_entries = Scanner.scan_folder(menu_path)
      expect(list_of_entries).to match_array(%w[entry1 entry2])
    end
  end

  describe 'handling non-existent directories' do
    it 'raises an exception' do
      expect { Scanner.scan_folder(non_existent_path) }.to raise_error(RuntimeError, /Directory does not exists!/)
    end
  end

  describe 'scanning files in folders' do
    it 'returns the list of files for entry1' do
      list_of_files = Scanner.scan_files(entry1_path)
      expect(list_of_files).to match_array(%w[task1.rb task2.rb])
    end

    it 'returns the list of files for entry2' do
      list_of_files = Scanner.scan_files(entry2_path)
      expect(list_of_files).to match_array(%w[task1.rb])
    end
  end
end
