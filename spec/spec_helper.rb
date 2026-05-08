require 'rspec'
require 'simplecov'
require 'colorize'
require 'stringio'

SimpleCov.start do
  add_filter '/spec/'

  minimum_coverage 90

  add_group 'Git Support', 'lib/git-support'
  add_group 'Installation Support', 'lib/installation-support'
  add_group 'Utils', 'lib/utils'
end

module OutputSilencer
  def silence_output
    original_stdout = $stdout
    original_stderr = $stderr

    $stdout = StringIO.new
    $stderr = StringIO.new

    yield
  ensure
    $stdout = original_stdout
    $stderr = original_stderr
  end
end

RSpec.configure do |config|
  config.include OutputSilencer

  config.expect_with :rspec do |expectations|
    expectations.include_chain_clauses_in_custom_matcher_descriptions = true
  end

  config.mock_with :rspec do |mocks|
    mocks.verify_partial_doubles = true
  end

  config.shared_context_metadata_behavior = :apply_to_host_groups

  config.disable_monkey_patching!

  config.order = :random
  Kernel.srand config.seed

  config.color = true

  # Hide default rspec formatter output
  config.output_stream = File.open(File::NULL, 'w')

  config.example_status_persistence_file_path = '.rspec_status'

  config.filter_run_when_matching :focus

  config.before(:suite) do
    puts
    puts '═' * 80
    puts 'RSPEC TEST SUITE'.light_blue.bold
    puts '═' * 80
    puts
  end

  config.around(:example) do |example|
    start_time = Time.now

    description = example.full_description

    description = description
      .gsub('AddWorkflow', 'add-workflow')
      .gsub('InstallationSupport::PackageManager', 'package-manager')
      .gsub('#', ' → ')
      .gsub(/\s+/, ' ')
      .strip

    begin
      silence_output do
        example.run
      end

      duration = ((Time.now - start_time) * 1000).round(2)

      if example.exception.nil?
        puts "→ #{description} ".light_black +
             'PASSED'.green +
             " (#{duration}ms)".light_black
      else
        puts "→ #{description} ".light_black +
             'FAILED'.red +
             " (#{duration}ms)".light_black
      end
    rescue StandardError
      puts "→ #{description} FAILED".red
      raise
    end
  end

  config.after(:example) do |example|
    next unless example.exception

    puts
    puts '─' * 80
    puts 'FAILURE'.red.bold
    puts '─' * 80

    puts

    description = example.full_description

    description = description
      .gsub('AddWorkflow', 'add-workflow')
      .gsub('InstallationSupport::PackageManager', 'package-manager')
      .gsub('#', ' → ')
      .gsub(/\s+/, ' ')
      .strip

    puts description.light_red

    puts
    puts example.exception.message.red
    puts

    if example.exception.backtrace
      puts 'Backtrace:'.yellow
      puts example.exception.backtrace.first(5).join("\n").light_black
    end

    puts
  end

  config.after(:suite) do
    puts
    puts '═' * 80
    puts 'TEST SUITE FINISHED'.green.bold
    puts '═' * 80

    coverage = SimpleCov.result.covered_percent.round(2)

    puts

    if coverage >= 90
      puts "Coverage: #{coverage}%".green.bold
    elsif coverage >= 80
      puts "Coverage: #{coverage}%".yellow.bold
    else
      puts "Coverage: #{coverage}%".red.bold
    end

    puts
  end
end