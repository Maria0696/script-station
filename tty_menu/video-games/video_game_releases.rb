class VideoGameReleases
  REQUIRED_ENV = %w[
    IGDB_CLIENT_ID
    IGDB_CLIENT_SECRET
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
  ].freeze

  MODULE_NAME = 'scripts.video_game_releases'.freeze

  def initialize(prompt)
    @prompt = prompt
  end

  def run
    return unless environment_ready?

    confirmed = @prompt.yes?(
      'This will send today releases to Telegram. Continue?'
    )

    return unless confirmed

    run_module(MODULE_NAME)
  end

  private

  def environment_ready?
    missing = REQUIRED_ENV.select do |variable|
      ENV[variable].nil? || ENV[variable].empty?
    end

    return true if missing.empty?

    puts 'Missing environment variables:'
    missing.each { |variable| puts "  - #{variable}" }

    false
  end

  def run_module(module_name)
    python = Gem.win_platform? ? 'py' : 'python3'

    success = system(
      python,
      '-m',
      module_name
    )

    return if success

    raise "Python module failed: #{module_name}"
  end
end
