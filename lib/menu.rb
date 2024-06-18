require './lib/utils/prompt'
require './lib/utils/goto'
require './lib/scanner/scanner'
require './lib/utils/utils'
require 'colorize'

Dir['./tty_menu/*/*'].sort.each do |file|
  require file
end

# rubocop:disable Metrics/AbcSize
class Menu
  def self.startup
    Utils.print_banner
    prompt = Prompt.new.prompt

    list_of_folders = Scanner.scan_folder('./tty_menu')

    step do
      project_selected = prompt.select('Which type of operation do you want to perform?') do |project|
        list_of_folders.each do |project_name|
          project.choice project_name
        end
      end
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
    end
  end
end
# rubocop:enable Metrics/AbcSize
