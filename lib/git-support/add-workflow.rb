require 'json'
require 'net/http'
require 'fileutils'
require 'open3'
require 'securerandom'
require 'colorize'

class AddWorkflow
  def initialize(prompt)
    @prompt = prompt
  end

  def run
    org = ask('GitHub organization')
    github_token = ask('GitHub token')
    repo_list_path = ask('Path to repo list file')
    workflow_template_path = ask('Path to workflow template')
    branch_suffix = ask('Branch suffix')

    dry_run = @prompt.yes?('Do you want to run in dry-run mode?')

    unless File.exist?(repo_list_path)
      puts
      puts "Repo list file not found: #{repo_list_path}".red
      return
    end

    unless File.exist?(workflow_template_path)
      puts
      puts "Workflow template not found: #{workflow_template_path}".red
      return
    end

    workflow_filename = File.basename(workflow_template_path)
    workflow_path = ".github/workflows/#{workflow_filename}"

    repos = File.readlines(repo_list_path, chomp: true)

    repos.each do |repo|
      repo = repo.strip

      next if repo.empty?
      next if repo.start_with?('#')

      puts
      puts "Processing repo: #{org}/#{repo}".light_blue

      branch_name = "add-workflow-#{branch_suffix}-#{Time.now.to_i}-#{SecureRandom.hex(4)}"

      if dry_run
        puts "[DRY RUN] Would clone #{org}/#{repo}".yellow
        puts "[DRY RUN] Would create branch #{branch_name}".yellow
        puts "[DRY RUN] Would add #{workflow_path}".yellow
        puts '[DRY RUN] Would commit, push, and open PR'.yellow
        next
      end

      FileUtils.rm_rf(repo)

      begin
        clone_repository(org, repo)

        Dir.chdir(repo) do
          default_branch = default_branch_name

          create_branch(branch_name, default_branch)

          FileUtils.mkdir_p(File.dirname(workflow_path))

          FileUtils.cp(
            File.expand_path(workflow_template_path, '..'),
            workflow_path
          )

          execute("git add #{workflow_path}")
          execute("git commit -m \"Add workflow #{workflow_filename}\"")
          execute("git push origin #{branch_name}")

          create_pull_request(
            org: org,
            repo: repo,
            github_token: github_token,
            branch_name: branch_name,
            default_branch: default_branch,
            workflow_filename: workflow_filename
          )
        end
      rescue StandardError => error
        puts
        puts "Error processing #{repo}".red
        puts error.message.red
      ensure
        Dir.chdir('..') if Dir.pwd.end_with?(repo)
        FileUtils.rm_rf(repo)
      end
    end
  end

  private

  def ask(question)
    loop do
      answer = @prompt.ask("#{question}: ")

      return answer.strip unless answer.nil? || answer.strip.empty?

      print "\e[1A"
      print "\e[2K"

      puts "#{question}: #{'This field cannot be empty'.red}"
    end
  end

  def execute(command)
    puts
    puts "Executing: #{command}".cyan

    stdout, stderr, status = Open3.capture3(command)

    unless status.success?
      puts stderr.red
      raise "Command failed: #{command}"
    end

    stdout
  end

  def clone_repository(org, repo)
    execute("git clone https://github.com/#{org}/#{repo}.git")
  end

  def default_branch_name
    `git remote show origin | awk '/HEAD branch/ {print $NF}'`.strip
  end

  def create_branch(branch_name, default_branch)
    execute("git checkout -b #{branch_name} origin/#{default_branch}")
  end

  def create_pull_request(org:, repo:, github_token:, branch_name:, default_branch:, workflow_filename:)
    uri = URI("https://api.github.com/repos/#{org}/#{repo}/pulls")

    payload = {
      title: "Add workflow: #{workflow_filename}",
      head: branch_name,
      base: default_branch,
      body: "Add workflow #{workflow_filename} via automation"
    }

    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    request = Net::HTTP::Post.new(uri.path)

    request['Authorization'] = "token #{github_token}"
    request['Accept'] = 'application/vnd.github+json'
    request['Content-Type'] = 'application/json'

    request.body = payload.to_json

    response = http.request(request)

    body = JSON.parse(response.body)

    if body['html_url']
      puts
      puts "→ PR created: #{body['html_url']}".green
    elsif body['errors']
      errors = body['errors']
        .map { |error| error['message'] || error.to_s }
        .join(', ')

      if errors.include?('A pull request already exists')
        puts
        puts '→ Pull request already exists'.yellow
      else
        puts
        puts '→ Failed to create PR'.red
        puts response.body.red
      end
    else
      puts
      puts '→ Failed to create PR'.red
      puts response.body.red
    end
  end
end
