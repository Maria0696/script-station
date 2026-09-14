class WatchlistMonitor
  REQUIRED_ENV = %w[
    IGDB_CLIENT_ID
    IGDB_CLIENT_SECRET
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
  ].freeze

  def initialize(prompt)
    @prompt = prompt
  end

  def run
    return unless environment_ready?

    confirmed = @prompt.yes?(
      'Check the watchlist for release changes?'
    )

    return unless confirmed

    run_script('scripts/watchlist_monitor.py')
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

  def run_script(script)
    python = Gem.win_platform? ? 'py' : 'python3'

    success = system(
      python,
      script
    )

    raise "Python script failed: #{script}" unless success
  end
end
