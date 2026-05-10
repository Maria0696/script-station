require './lib/utils/prompt'
require './lib/git-support/add-workflow'

class GithubManager
  def initialize(prompt)
    @prompt = prompt
  end

  def run
    github_scripts = {
      'Add workflow' => AddWorkflow,
    }

    selected_script = @prompt.select('Which GitHub script do you want to execute?', filter: true) do |menu|
      github_scripts.each do |script_name, script_class|
        menu.choice script_name, script_class
      end
    end

    return if selected_script.nil?

    selected_script.new(@prompt).run
  end
end