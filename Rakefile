require 'rake/testtask'
require 'rubocop/rake_task'
require './lib/menu'

desc 'Starting up Script Stations'
task :start_tool do |_task, _task_args|
  Menu.startup
rescue TTY::Reader::InputInterrupt
  puts "\nExiting Script Station".red
rescue StandardError => e
  puts 'Finished with Exception'.red
  puts e.message.to_s.red
end

desc 'Run all tests'
task test: %w[test:spec]

begin
  RuboCop::RakeTask.new
rescue LoadError
  puts 'RuboCop is not available'
end

namespace :test do
  begin
    require 'rspec/core/rake_task'
    RSpec::Core::RakeTask.new(:spec)
  rescue LoadError
    puts 'RSpec is not available'
  end
end
