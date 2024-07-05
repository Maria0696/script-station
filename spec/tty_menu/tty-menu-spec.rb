require './lib/scanner/scanner'

RSpec.describe 'concourse support tasks should work properly' do
  it 'Should retrieve list of tty menu folders' do
    list_of_entries = Scanner.scan_folder('./spec/fixtures/menu')
    expect(list_of_entries).to eq(%w[entry1 entry2])
  end

  it 'should throw exception when dir does not exist' do
    expect { Scanner.scan_folder('does_not_exist') }.to raise_error(RuntimeError)
  end

  it 'should return list when scanning files' do
    list_of_files = Scanner.scan_files('./spec/fixtures/menu/entry1')
    expect(list_of_files).to eq(%w[task1.rb task2.rb])

    list_of_files = Scanner.scan_files('./spec/fixtures/menu/entry2')
    expect(list_of_files).to eq(%w[task1.rb])
  end
end
