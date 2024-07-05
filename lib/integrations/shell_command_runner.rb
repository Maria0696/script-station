# frozen_string_literal: false

require 'colorize'
require 'errors'
require 'open3'

module Integrations
  class ShellCommandError < StandardError; end

  class ShellCommandRunner
    class << self
      # Executes a shell command in the specified directory
      def run(cmd:, chdir: Dir.pwd, hide_output: false, sanitize_credentials: false, quiet: false)
        puts "Running Shell Command (#{chdir}): #{cmd}" unless quiet

        output = nil
        Open3.popen3(cmd, chdir: chdir) do |_, stdout, stderr, wait_thr|
          out_thr, output = read_stdout(stdout, hide_output, sanitize_credentials)
          err_thr, error_output = read_stderr(stderr, hide_output)

          # Wait for all output to be read
          out_thr.join
          err_thr.join

          # Verify the output code of the command
          raise ShellCommandError, error_output unless wait_thr.value.success?
        end
        output
      end

      private

      # Reads and processes the standard output of the command
      def read_stdout(stdout, hide_output, sanitize_credentials)
        output = ''
        thread = Thread.new do
          stdout.each_line do |line|
            output << line
            line = sanitize_line(line) if sanitize_credentials
            puts 'OUT: '.colorize(:blue) + line unless hide_output
          end
        end
        [thread, output]
      end

      # Reads and processes the error output from the command
      def read_stderr(stderr, hide_output)
        error_output = ''
        thread = Thread.new do
          stderr.each_line do |line|
            error_output << line
            puts 'ERR: '.colorize(:red) + line unless hide_output
          end
        end
        [thread, error_output]
      end

      # Sanitizes a line of text by removing sensitive credentials
      def sanitize_line(line)
        sensitive_words = %w[ClientId client-id client-secret ClientSecret]
        sensitive_words.each do |word|
          line.gsub!(/(#{word}:?\s*["']?).+?(["']?,?)/, '\1*****\2') if line.include?(word)
        end
        line
      end
    end
  end
end

class ShellCommandError < StandardError; end
