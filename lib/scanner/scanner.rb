
class Scanner
  # Scans the directory and returns a sorted list of subdirectories
  def self.scan_folder(dir)
    scan(dir) { |file| File.directory?(File.join(dir, file)) }
  end

  # Scans the directory and returns a sorted list of files
  def self.scan_files(dir)
    scan(dir) { |file| File.file?(File.join(dir, file)) }
  end

  private

  # Common scan method to filter and sort directory contents
  def self.scan(dir)
    raise 'Directory does not exists!' unless Dir.exist?(dir)

    Dir.children(dir).select { |file| yield(file) }.sort
  end
end
