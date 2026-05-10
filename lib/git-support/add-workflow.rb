require 'json'
require 'net/http'
require 'fileutils'
require 'open3'
require 'securerandom'
require 'colorize'
require 'yaml'

class AddWorkflow
  LOG_FILE = 'logs/add_workflow.log'.freeze

  def initialize(prompt)
    @prompt = prompt
    FileUtils.mkdir_p('logs')
  end

  def run
    config_mode = @prompt.yes?('Do you want to use a config.yml file?')

    config_mode ? load_config : manual_input

    return if !@dry_run && !validate_token

    unless File.exist?(@repo_list_path)
      puts
      puts "Repo list file not found: #{@repo_list_path}".red
      return
    end

    unless File.exist?(@workflow_template_path)
      puts
      puts "Workflow template not found: #{@workflow_template_path}".red
      return
    end

    workflow_filename = File.basename(@workflow_template_path)
    workflow_path = ".github/workflows/#{workflow_filename}"

    repos = File.readlines(@repo_list_path, chomp: true)

    puts
    puts "Found #{repos.count} repositories".green

    repos.each_with_index do |repo, index|
      repo = repo.strip

      next if repo.empty?
      next if repo.start_with?('#')

      puts
      puts "[#{index + 1}/#{repos.count}] Processing repo: #{@org}/#{repo}".light_blue

      log("Processing #{@org}/#{repo}")

      branch_name = build_branch_name

      if @dry_run
        dry_run_output(repo, branch_name, workflow_path)
        next
      end

      process_repository(
        repo: repo,
        workflow_filename: workflow_filename,
        workflow_path: workflow_path,
        branch_name: branch_name
      )
    end

    puts
    puts 'Finished processing repositories'.green
  end

  private

  def manual_input
    @org = ask('GitHub organization')
    @github_token = ask('GitHub token')
    @repo_list_path = ask('Path to repo list file')
    @workflow_template_path = ask('Path to workflow template')
    @branch_suffix = ask('Branch suffix')
    @dry_run = @prompt.yes?('Do you want to run in dry-run mode?')
  end

  def load_config
    config_path = ask('Path to config.yml')

    unless File.exist?(config_path)
      puts
      puts "Config file not found: #{config_path}".red
      exit
    end

    config = YAML.load_file(config_path)

    @org = config['org']
    @github_token = config['github_token']
    @repo_list_path = config['repo_list_path']
    @workflow_template_path = config['workflow_template_path']
    @branch_suffix = config['branch_suffix']
    @dry_run = config['dry_run'] || false

    puts
    puts 'Configuration loaded successfully'.green
  end

  def ask(question)
    loop do
      answer = @prompt.ask("#{question}: ")

      return answer.strip unless answer.nil? || answer.strip.empty?

      print "\e[1A"
      print "\e[2K"

      puts "#{question}: #{'This field cannot be empty'.red}"
    end
  end

  def validate_token
    puts
    puts 'Validating GitHub token...'.cyan

    uri = URI('https://api.github.com/user')

    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    request = Net::HTTP::Get.new(uri.path)
    request['Authorization'] = "token #{@github_token}"

    response = http.request(request)

    if response.code.to_i == 200
      puts 'GitHub token validated successfully'.green
      true
    else
      puts 'Invalid GitHub token'.red
      false
    end
  end

  def build_branch_name
    "add-workflow-#{@branch_suffix}-#{Time.now.to_i}-#{SecureRandom.hex(4)}"
  end

  def dry_run_output(repo, branch_name, workflow_path)
    puts "[DRY RUN] Would clone #{@org}/#{repo}".yellow
    puts "[DRY RUN] Would create branch #{branch_name}".yellow
    puts "[DRY RUN] Would add #{workflow_path}".yellow
    puts '[DRY RUN] Would commit, push, and open PR'.yellow
  end

  def process_repository(repo:, workflow_filename:, workflow_path:, branch_name:)
    FileUtils.rm_rf(repo)

    begin
      with_retry do
        clone_repository(repo)
      end

      Dir.chdir(repo) do
        default_branch = default_branch_name

        with_retry do
          create_branch(branch_name, default_branch)
        end

        FileUtils.mkdir_p(File.dirname(workflow_path))

        FileUtils.cp(
          File.expand_path(@workflow_template_path, '..'),
          workflow_path
        )

        execute("git add #{workflow_path}")
        execute("git commit -m \"Add workflow #{workflow_filename}\"")
        execute("git push origin #{branch_name}")

        create_pull_request(
          repo: repo,
          branch_name: branch_name,
          default_branch: default_branch,
          workflow_filename: workflow_filename
        )
      end

      puts "Finished #{@org}/#{repo}".green
      log("SUCCESS #{@org}/#{repo}")
    rescue StandardError => e
      puts
      puts "Error processing #{repo}".red
      puts e.message.red

      log("ERROR #{@org}/#{repo} - #{e.message}")
    ensure
      Dir.chdir('..') if Dir.pwd.end_with?(repo)
      FileUtils.rm_rf(repo)
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

  def clone_repository(repo)
    execute("git clone https://github.com/#{@org}/#{repo}.git")
  end

  def default_branch_name
    `git remote show origin | awk '/HEAD branch/ {print $NF}'`.strip
  end

  def create_branch(branch_name, default_branch)
    execute("git checkout -b #{branch_name} origin/#{default_branch}")
  end

  def create_pull_request(repo:, branch_name:, default_branch:, workflow_filename:)
    return dry_run_pull_request(repo, branch_name) if @dry_run

    response = github_pull_request_request(
      repo: repo,
      branch_name: branch_name,
      default_branch: default_branch,
      workflow_filename: workflow_filename
    )

    handle_pull_request_response(response, repo)
  end

  def github_pull_request_request(repo:, branch_name:, default_branch:, workflow_filename:)
    uri = URI("https://api.github.com/repos/#{@org}/#{repo}/pulls")

    request = Net::HTTP::Post.new(uri.path)

    request['Authorization'] = "token #{@github_token}"
    request['Accept'] = 'application/vnd.github+json'
    request['Content-Type'] = 'application/json'

    request.body = pull_request_payload(
      branch_name: branch_name,
      default_branch: default_branch,
      workflow_filename: workflow_filename
    ).to_json

    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true

    http.request(request)
  end

  def pull_request_payload(branch_name:, default_branch:, workflow_filename:)
    {
      title: "Add workflow: #{workflow_filename}",
      head: branch_name,
      base: default_branch,
      body: pull_request_body(workflow_filename)
    }
  end

  def pull_request_body(workflow_filename)
    <<~BODY
      Add workflow #{workflow_filename} via automation.

      Generated automatically by script-station.
    BODY
  end

  def handle_pull_request_response(response, repo)
    body = JSON.parse(response.body)

    return log_pull_request_success(body) if body['html_url']

    handle_pull_request_error(body, response, repo)
  end

  def log_pull_request_success(body)
    puts
    puts "→ PR created: #{body['html_url']}".green

    log("PR CREATED #{body['html_url']}")
  end

  def handle_pull_request_error(body, response, repo)
    puts
    if pull_request_already_exists?(body)
      puts '→ Pull request already exists'.yellow

      log("PR ALREADY EXISTS #{@org}/#{repo}")
    else
      puts '→ Failed to create PR'.red
      puts response.body.red

      log("FAILED PR #{@org}/#{repo}")
    end
  end

  def pull_request_already_exists?(body)
    body['errors']&.any? do |error|
      error['message']&.include?('A pull request already exists')
    end
  end

  def dry_run_pull_request(repo, branch_name)
    puts "[DRY RUN] Would create PR for #{repo} from #{branch_name}".yellow
  end

  def with_retry(max_attempts = 3)
    attempts = 0

    begin
      attempts += 1
      yield
    rescue StandardError => e
      if attempts < max_attempts
        puts
        puts "Retrying... Attempt #{attempts}/#{max_attempts}".yellow
        sleep(2)
        retry
      end

      raise e
    end
  end

  def log(message)
    File.open(LOG_FILE, 'a') do |file|
      file.puts("[#{Time.now}] #{message}")
    end
  end
end
