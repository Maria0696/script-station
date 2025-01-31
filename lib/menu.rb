require './lib/utils/prompt'
require './lib/utils/goto'
require './lib/scanner/scanner'
require './lib/utils/utils'
require 'colorize'

# Dynamically require all files in subdirectories of ./tty_menu
Dir['./tty_menu/*/*'].sort.each do |file|
  require file
end

# Dynamically require all files in subdirectories of ./tty_menu
class Menu
  def self.startup
    Utils.print_banner
    prompt = Prompt.new.prompt

    list_of_folders = Scanner.scan_folder('./tty_menu')

    # First step: Select the type of operation
    step do
      project_selected = prompt.select('Which type of operation do you want to perform?') do |project|
        list_of_folders.each do |project_name|
          project.choice project_name
        end
      end

      # Second step: Select the task
      step do
        list_of_tasks = Scanner.scan_files('./tty_menu/'.concat(project_selected))
        task_selected = prompt.select('Which task do you want to work with?') do |task|
          list_of_tasks.each do |task_name|
            task.choice Utils.wizard_format_task_name(task_name)
          end
        end

        unless task_selected.nil?
          selected_class = Object.const_get Utils.convert_to_class_name(task_selected)
          selected_class.new(prompt).run
        end
      end
      # End second step
    end
    # End first step
  end
end
