# Script-Station

[![Quality Checks](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml/badge.svg)](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml)

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

## Available Scripts

### GitHub support → Add workflow

Drop the same workflow into a bunch of repos and open a PR in each, all in one go. From the menu: `git-support` → `Github Manager` → `Add workflow`.

Answer the prompts, or hand it a `config.yml`:

```yaml
org: my-org
github_token: ghp_xxx       # token with 'repo' scope
repo_list_path: repos.txt   # one repo name per line
workflow_template_path: templates/workflows/update-readme-profile.yml
branch_suffix: ci
dry_run: true               # true = just preview, touch nothing
```

Flip `dry_run: false` to really clone, branch, commit, push and open the PRs (the token is masked in logs). **Never commit a real `config.yml` — it holds your token.**

### Daily Video Game Releases (Telegram bot)

`scripts/video_game_releases.py` checks IGDB for today's releases and pings them to Telegram — automatically every day (or on demand) via the `Daily Video Game Releases` Action. Just add four secrets: `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Testing

Run the test suite and the linter:

`bundle exec rspec`   (or `rake test`)

`bundle exec rubocop`

Both run automatically in CI (`Quality Checks`). The suite enforces a coverage gate: the build fails if total coverage drops below **90%** or any single file below **80%**. An HTML coverage report is uploaded as a build artifact (`coverage-report`).

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