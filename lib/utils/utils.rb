require 'fileutils'
require 'active_support'
require 'active_support/core_ext'

class Utils
  class << self
    DATE_PATTERN_ = '%Y%m%d%H%M%S'.freeze

    def file_name(environment_name, org_name, org_space, project_folder, extension = 'json')
      folder = "#{OUTPUT_DIR}/#{project_folder}/"
      FileUtils.mkdir_p(folder) unless Dir.exist?(folder)
      "#{folder}#{now_date_time}-#{environment_name}-#{org_name}-#{org_space}.#{extension}"
    end

    def create_file(project_folder, file_name)
      folder = "#{OUTPUT_DIR}/#{project_folder}/"
      FileUtils.mkdir_p(folder) unless Dir.exist?(folder)
      "#{folder}#{file_name}"
    end

    def wizard_format_task_name(task_name)
      task_name.capitalize.chomp('.rb').gsub('_', ' ')
    end

    def convert_to_file_name(wizard_formatted_task_name)
      wizard_formatted_task_name.downcase.gsub(' ', '_').concat('.rb')
    end

    def convert_to_operation_name(wizard_formatted_task_name)
      wizard_formatted_task_name.downcase.gsub(' ', '_')
    end

    def operation_name_to_wizard_name(wizard_formatted_task_name)
      wizard_formatted_task_name.gsub('_', ' ').capitalize
    end

    def convert_to_class_name(wizard_formatted_task_name)
      wizard_formatted_task_name.titleize.gsub(' ', '')
    end

    def print_banner
      puts <<-'BANNER'
     ____            _       _        ____  _        _   _
    / ___|  ___ _ __(_)_ __ | |_     / ___|| |_ __ _| |_(_) ___  _ __
    \___ \ / __| '__| | '_ \| __|    \___ \| __/ _` | __| |/ _ \| '_ \
     ___) | (__| |  | | |_) | |_      ___) | || (_| | |_| | (_) | | | |
    |____/ \___|_|  |_| .__/ \__|    |____/ \__\__,_|\__|_|\___/|_| |_|
                      |_|
      BANNER
        .blue
      puts 'Use arrows to navigate and enter to select option'.yellow
    end

    def now_date_time
      Time.now.utc.strftime(DATE_PATTERN_)
    end
  end
end
