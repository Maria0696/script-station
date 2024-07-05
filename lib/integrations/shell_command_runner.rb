# frozen_string_literal: false

require 'colorize'
require 'errors'
require 'open3'

module Integrations
  class ShellCommandError < StandardError; end

  class ShellCommandRunner
    class << self
      def run(cmd:, chdir: Dir.pwd, hide_output: false, sanitize_credentials: false, quiet: false)
        puts "Running Shell Command (#{chdir}): #{cmd}" unless quiet

        output = nil
        Open3.popen3(cmd, chdir: chdir) do |_, stdout, stderr, wait_thr|
          out_thr, output = read_stdout(stdout, hide_output, sanitize_credentials)

          in_thr, error_output = read_stderr(stderr, hide_output)
          # Gotta wait for all output to be read from the shell command
          in_thr.join
          out_thr.join

          raise ShellCommandError, error_output unless wait_thr.value.success?
        end
        output
      end

      private

      def read_stdout(stdout, hide_output, sanitize_credentials)
        out = ''
        thr = Thread.new do
          while (line = stdout.gets)
            out << line
            if sanitize_credentials && %w[ClientId client-id client-secret ClientSecret].any? { |word| line.include?(word) }
              line = line.gsub! line[line.index(':') + 1, line.length - 1], ' "*****",'
            end
            puts 'OUT: '.colorize(:blue) + line unless hide_output
          end
        end
        [thr, out]
      end

      def read_stderr(stderr, hide_output)
        err = ''
        thr = Thread.new do
          while (line = stderr.gets)
            err << line
            puts 'ERR: '.colorize(:red) + line unless hide_output
          end
        end
        [thr, err]
      end
    end
  end
end

class ShellCommandError < StandardError; end
