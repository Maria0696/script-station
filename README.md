# Script-Station

Script-Station is an interactive script repository designed to simplify and automate tasks through an intuitive and user-friendly interface.

## Description

Script-Station centralizes a collection of scripts that enable users to execute various actions interactively. From advanced configurations to daily tasks, Script-Station is designed to streamline script execution with just a few simple steps.

## Features

- **Interactive Interface:** Execute scripts using a friendly user interface.
- **Script Centralization:** Store a variety of scripts for different purposes in one place.
- **Ease of Use:** Simplify complex tasks with guided operations.
- **Customization:** Adapt and extend functionality by adding new scripts.

## Requirements

- Ruby (refer to `Gemfile` for specific version)

## Installation

1. Clone this repository:

   `git clone https://github.com/Maria0696/script-station.git`

   `cd script-station`
   
2. Install dependencies specified in the Gemfile:

    `bundle install`

## Usage

1. Start Script-Station interface:

    `rake start_tool`

    Or set your shell configuration file like ".bash_profile" or "~/.zshrc-" as follow: 

    - Set alias:

      `alias script-station='cd ~/workspace/script-station;rake start_tool`

    - Source configuration file:

      `source ~/.zshrc`

    - And call script-station:

      `script-station`

2. Select the script you wish to execute from the interactive menu.

3. Follow on-screen instructions to complete the execution of the selected script.

## Contributing

Contributions are welcome! If you wish to add new scripts or improve existing functionality, please submit a pull request.

## Project Structure

The project follows an organized structure for scripts and additional functionalities:

1. Create a new folder under tty-menu with name {functionality}-support

2. Create a new ruby file in that folder like {name}.rb. This file will contain the questions for the menu

3. Create a folder with the same structure ({functionality}-support) inside of lib/ this folder is to create the tasks that will be executed from the menu

```
script-station
├── lib
│   ├── <functionality>_support
│   │   ├── <name>.rb
│   │   └── ...
│   └── ...
└── tty_menu
    ├── <functionality>_support
    │   ├── <name>.rb
    │   └── ...
    └── ...
```
## About the menu

Script-Station utilizes the Step class to manage the interactive menu. Here's an example of how a step is structured:

```
step do
  # Logic to present options to the user
end
```

## Backward Navigation Support

To navigate back in the interactive menu, steps should be properly nested:

```
step do
  # First level of questions and options
  step do
    # Second level of questions and options
  end
end
```