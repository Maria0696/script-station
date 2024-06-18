require 'tty-prompt'

prompt = TTY::Prompt.new

options = ['Option 1', 'Option 2', 'Option 3']
user_choice = prompt.select("Choose an option:", options)

puts "You chose: #{user_choice}"
