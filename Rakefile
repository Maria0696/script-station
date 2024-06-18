require 'rake/testtask'
require 'rubocop/rake_task'
require './lib/menu'

desc 'Starting up Script Stations'
task :start_tool do |_task, _task_args|
  Menu.startup
rescue TTY::Reader::InputInterrupt
  puts "\n Exiting Script Station".red
rescue StandardError => e
  puts 'Finish with Exception'.red
  puts e.message.to_s.red
end

desc 'Run all tests'
task test: %w[test:spec]

begin
  require 'rubocop/rake_task'
  RuboCop::RakeTask.new
rescue StandardError
  # no rubocop available
end

namespace :test do
  require 'rspec/core/rake_task'
  RSpec::Core::RakeTask.new(:spec)
rescue LoadError
  # ignored
end
