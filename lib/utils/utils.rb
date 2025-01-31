require 'fileutils'
require 'active_support'
require 'active_support/core_ext'
require 'colorize'

class Utils
  OUTPUT_DIR = 'output'
  DATE_PATTERN_ = '%Y%m%d%H%M%S'

  class << self
    # Formats a task name to be more readable by capitalizing it, removing the '.rb' suffix, and replacing underscores with spaces
    def wizard_format_task_name(task_name)
      task_name.capitalize.chomp('.rb').gsub('_', ' ')
    end

    # Converts a wizard formatted task name to a file name by downcasing it, replacing spaces with underscores, and adding the '.rb' suffix
    def convert_to_file_name(wizard_formatted_task_name)
      wizard_formatted_task_name.downcase.gsub(' ', '_').concat('.rb')
    end

    # Converts a wizard formatted task name to an operation name by downcasing it and replacing spaces with underscores
    def convert_to_operation_name(wizard_formatted_task_name)
      wizard_formatted_task_name.downcase.gsub(' ', '_')
    end

    # Converts an operation name to a wizard formatted task name by replacing underscores with spaces and capitalizing it
    def operation_name_to_wizard_name(wizard_formatted_task_name)
      wizard_formatted_task_name.gsub('_', ' ').capitalize
    end

    # Converts a wizard formatted task name to a class name by titleizing it and removing spaces
    def convert_to_class_name(wizard_formatted_task_name)
      wizard_formatted_task_name.titleize.gsub(' ', '')
    end

    # Prints an ASCII banner and navigation instructions to the console
    def print_banner
      puts <<-'BANNER'
     ____            _       _        ____  _        _   _
    / ___|  ___ _ __(_)_ __ | |_     / ___|| |_ __ _| |_(_) ___  _ __
    \___ \ / __| '__| | '_ \| __|    \___ \| __/ _` | __| |/ _ \| '_ \
     ___) | (__| |  | | |_) | |_      ___) | || (_| | |_| | (_) | | | |
    |____/ \___|_|  |_| .__/ \__|    |____/ \__\__,_|\__|_|\___/|_| |_|
                      |_|
      BANNER
      puts 'Use arrows to navigate and enter to select option'.yellow
    end

    # Returns the current date and time in UTC formatted as '%Y%m%d%H%M%S'
    def now_date_time
      Time.now.utc.strftime(DATE_PATTERN_)
    end
  end
end
