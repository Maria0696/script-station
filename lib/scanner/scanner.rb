class Scanner
  def self.scan_folder(dir)
    raise 'Directory does not exists!' unless Dir.exist?(dir)

    Dir.children(dir).select { |file| File.directory? File.join(dir, file) }.sort
  end

  def self.scan_files(dir)
    raise 'Directory does not exists!' unless Dir.exist?(dir)

    Dir.children(dir).select { |file| File.file? File.join(dir, file) }.sort
  end
end
