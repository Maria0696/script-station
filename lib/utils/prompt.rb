require 'tty-prompt'
require './lib/utils/utils'

class Prompt
  def initialize
    @prompt = TTY::Prompt.new

    @prompt.on(:keyleft) do |_event|
      @prompt.trigger(:keydown)
      system 'clear'
      system 'cls'
      Utils.print_banner
      puts "\n"
      return_previous
    end

    @prompt.on(:keyright) do |_event|
      @prompt.trigger(:keyenter)
    end
  end

  attr_reader :prompt
end
