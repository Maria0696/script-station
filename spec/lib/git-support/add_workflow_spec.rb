require 'spec_helper'
require 'fileutils'
require 'yaml'
require 'webmock/rspec'
require './lib/git-support/add-workflow'

RSpec.describe AddWorkflow do
  let(:prompt) { instance_double('Prompt') }

  subject(:script) { described_class.new(prompt) }

  before do
    FileUtils.mkdir_p('logs')
  end

  after do
    FileUtils.rm_rf('logs')
    FileUtils.rm_f('repos.txt')
    FileUtils.rm_f('ci.yml')
    FileUtils.rm_f('config.yml')
  end

  describe '#run' do
    context 'when using config.yml in dry run mode' do
      before do
        File.write(
          'repos.txt',
          <<~TEXT
            repo-one
            repo-two
          TEXT
        )

        File.write(
          'ci.yml',
          <<~YAML
            name: CI

            on:
              pull_request:
          YAML
        )

        File.write(
          'config.yml',
          {
            'org' => 'test-org',
            'github_token' => 'fake-token',
            'repo_list_path' => 'repos.txt',
            'workflow_template_path' => 'ci.yml',
            'branch_suffix' => 'ci',
            'dry_run' => true
          }.to_yaml
        )

        allow(prompt).to receive(:yes?)
          .and_return(true)

        allow(prompt).to receive(:ask)
          .and_return('config.yml')
      end

      it 'loads config successfully' do
        expect do
          script.run
        end.to output(/Configuration loaded successfully/).to_stdout
      end

      it 'processes repositories' do
        expect do
          script.run
        end.to output(/\[DRY RUN\]/).to_stdout
      end
    end

    context 'when config file does not exist' do
      before do
        allow(prompt).to receive(:yes?)
          .and_return(true)

        allow(prompt).to receive(:ask)
          .and_return('missing.yml')
      end

      it 'prints config error' do
        expect do
          script.run
        end.to raise_error(SystemExit)
      end
    end
  end

  describe '#ask' do
    it 'returns valid answer' do
      allow(prompt).to receive(:ask)
        .and_return('value')

      result = script.send(:ask, 'Question')

      expect(result).to eq('value')
    end

    it 'retries when empty value' do
      allow(prompt).to receive(:ask)
        .and_return('', 'valid')

      result = script.send(:ask, 'Question')

      expect(result).to eq('valid')
    end
  end

  describe '#manual_input' do
    before do
      allow(prompt).to receive(:ask)
        .and_return(
          'test-org',
          'token',
          'repos.txt',
          'ci.yml',
          'ci'
        )

      allow(prompt).to receive(:yes?)
        .and_return(true)
    end

    it 'loads manual input values' do
      script.send(:manual_input)

      expect(script.instance_variable_get(:@org)).to eq('test-org')
      expect(script.instance_variable_get(:@github_token)).to eq('token')
      expect(script.instance_variable_get(:@repo_list_path)).to eq('repos.txt')
    end
  end

  describe '#load_config' do
    before do
      File.write(
        'config.yml',
        {
          'org' => 'test-org',
          'github_token' => 'token',
          'repo_list_path' => 'repos.txt',
          'workflow_template_path' => 'ci.yml',
          'branch_suffix' => 'ci',
          'dry_run' => true
        }.to_yaml
      )

      allow(prompt).to receive(:ask)
        .and_return('config.yml')
    end

    it 'loads yaml config' do
      script.send(:load_config)

      expect(script.instance_variable_get(:@org)).to eq('test-org')
    end
  end

  describe '#validate_token' do
    before do
      script.instance_variable_set(:@github_token, 'token')
    end

    it 'returns true for valid token' do
      stub_request(:get, 'https://api.github.com/user')
        .to_return(status: 200)

      expect(script.send(:validate_token)).to eq(true)
    end

    it 'returns false for invalid token' do
      stub_request(:get, 'https://api.github.com/user')
        .to_return(status: 401)

      expect(script.send(:validate_token)).to eq(false)
    end
  end

  describe '#build_branch_name' do
    before do
      script.instance_variable_set(:@branch_suffix, 'ci')
    end

    it 'creates unique branch name' do
      branch_name = script.send(:build_branch_name)

      expect(branch_name).to include('add-workflow-ci')
    end
  end

  describe '#dry_run_output' do
    before do
      script.instance_variable_set(:@org, 'test-org')
    end

    it 'prints dry run output' do
      expect do
        script.send(
          :dry_run_output,
          'repo-one',
          'branch',
          '.github/workflows/ci.yml'
        )
      end.to output(/\[DRY RUN\]/).to_stdout
    end
  end

  describe '#log' do
    it 'writes log file' do
      script.send(:log, 'TEST MESSAGE')

      content = File.read('logs/add_workflow.log')

      expect(content).to include('TEST MESSAGE')
    end
  end

  describe '#with_retry' do
    it 'retries block' do
      attempts = 0

      expect do
        script.send(:with_retry, 3) do
          attempts += 1

          raise 'Temporary error' if attempts < 3
        end
      end.not_to raise_error

      expect(attempts).to eq(3)
    end

    it 'raises after max retries' do
      expect do
        script.send(:with_retry, 2) do
          raise 'Permanent error'
        end
      end.to raise_error('Permanent error')
    end
  end

  describe '#execute' do
    it 'runs command successfully' do
      allow(Open3).to receive(:capture3)
        .and_return(['success', '', double(success?: true)])

      result = script.send(:execute, 'echo test')

      expect(result).to eq('success')
    end

    it 'raises error when command fails' do
      allow(Open3).to receive(:capture3)
        .and_return(['', 'error', double(success?: false)])

      expect do
        script.send(:execute, 'bad command')
      end.to raise_error(/Command failed/)
    end

    it 'does not leak the token in the executing output' do
      script.instance_variable_set(:@github_token, 'secret-token')

      allow(Open3).to receive(:capture3)
        .and_return(['ok', '', double(success?: true)])

      expect do
        script.send(
          :execute,
          'git clone https://x-access-token:secret-token@github.com/o/r.git'
        )
      end.to output(/x-access-token:\*\*\*@/).to_stdout
    end

    it 'masks the token in the failure error message' do
      script.instance_variable_set(:@github_token, 'secret-token')

      allow(Open3).to receive(:capture3)
        .and_return(['', 'boom', double(success?: false)])

      expect do
        script.send(
          :execute,
          'git push https://x-access-token:secret-token@github.com/o/r.git'
        )
      end.to raise_error(%r{Command failed: git push https://x-access-token:\*\*\*@})
    end
  end

  describe '#mask_secrets' do
    it 'masks the github token in text' do
      script.instance_variable_set(:@github_token, 'secret-token')

      masked = script.send(
        :mask_secrets,
        'https://x-access-token:secret-token@github.com/o/r.git'
      )

      expect(masked).to eq('https://x-access-token:***@github.com/o/r.git')
    end

    it 'returns text unchanged when token is not set' do
      script.instance_variable_set(:@github_token, nil)

      expect(script.send(:mask_secrets, 'plain text')).to eq('plain text')
    end
  end

  describe '#clone_repository' do
    before do
      script.instance_variable_set(:@org, 'test-org')
      script.instance_variable_set(:@github_token, 'token')
    end

    it 'executes clone command with token authentication' do
      expect(script).to receive(:execute)
        .with('git clone https://x-access-token:token@github.com/test-org/repo-one.git')

      script.send(:clone_repository, 'repo-one')
    end
  end

  describe '#create_branch' do
    it 'executes branch creation command' do
      expect(script).to receive(:execute)
        .with('git checkout -b feature origin/main')

      script.send(:create_branch, 'feature', 'main')
    end
  end

  describe '#default_branch_name' do
    it 'returns default branch' do
      allow(script).to receive(:`)
        .and_return("main\n")

      branch = script.send(:default_branch_name)

      expect(branch).to eq('main')
    end
  end

  describe '#create_pull_request' do
    before do
      script.instance_variable_set(:@org, 'test-org')
      script.instance_variable_set(:@github_token, 'token')
    end

    it 'creates pull request successfully' do
      stub_request(:post, 'https://api.github.com/repos/test-org/repo-one/pulls')
        .to_return(
          status: 201,
          body: {
            html_url: 'https://github.com/test/pr/1'
          }.to_json,
          headers: { 'Content-Type' => 'application/json' }
        )

      expect do
        script.send(
          :create_pull_request,
          repo: 'repo-one',
          branch_name: 'branch',
          default_branch: 'main',
          workflow_filename: 'ci.yml'
        )
      end.to output(/PR created/).to_stdout
    end

    it 'handles existing pull request' do
      stub_request(:post, 'https://api.github.com/repos/test-org/repo-one/pulls')
        .to_return(
          status: 422,
          body: {
            errors: [
              {
                message: 'A pull request already exists'
              }
            ]
          }.to_json,
          headers: { 'Content-Type' => 'application/json' }
        )

      expect do
        script.send(
          :create_pull_request,
          repo: 'repo-one',
          branch_name: 'branch',
          default_branch: 'main',
          workflow_filename: 'ci.yml'
        )
      end.to output(/already exists/).to_stdout
    end
  end

  describe '#process_repository' do
    before do
      script.instance_variable_set(:@org, 'test-org')
      script.instance_variable_set(:@workflow_template_path, 'ci.yml')

      File.write('ci.yml', 'name: test')

      allow(script).to receive(:clone_repository)
      allow(script).to receive(:default_branch_name)
        .and_return('main')

      allow(script).to receive(:create_branch)
      allow(script).to receive(:execute)
      allow(script).to receive(:create_pull_request)

      allow(Dir).to receive(:chdir)
        .and_yield

      allow(FileUtils).to receive(:cp)
      allow(FileUtils).to receive(:mkdir_p)
      allow(FileUtils).to receive(:rm_rf)
    end

    it 'processes repository successfully' do
      expect do
        script.send(
          :process_repository,
          repo: 'repo-one',
          workflow_filename: 'ci.yml',
          workflow_path: '.github/workflows/ci.yml',
          branch_name: 'feature'
        )
      end.not_to raise_error
    end

    it 'handles processing errors' do
      allow(script).to receive(:clone_repository)
        .and_raise(StandardError.new('Clone failed'))

      expect do
        script.send(
          :process_repository,
          repo: 'repo-one',
          workflow_filename: 'ci.yml',
          workflow_path: '.github/workflows/ci.yml',
          branch_name: 'feature'
        )
      end.not_to raise_error
    end
  end
end
