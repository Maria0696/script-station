# Script-Station

[![Quality Checks](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml/badge.svg)](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml)

Script-Station is a collection of automation tools and scripts built with Ruby and Python.

It includes an interactive Ruby interface, GitHub automation utilities, Telegram bots, video game release tracking, watchlist monitoring, and automated quality checks.

## Features

- **Interactive Ruby interface:** Run utilities through a guided terminal menu.
- **GitHub automation:** Automate repetitive repository tasks.
- **Telegram bots:** Huginn and Heimdall provide gaming and monitoring features.
- **Video game tracking:** Retrieve release information from IGDB.
- **Watchlist monitoring:** Detect changes in release dates and platforms.
- **Automated workflows:** Run scheduled tasks with GitHub Actions.
- **Quality checks:** Ruby and Python tests are organized under a shared test structure.

## Requirements

### Ruby

Ruby is used by the interactive Script-Station tools.

Refer to the `Gemfile` and `Gemfile.lock` for the required dependencies.

### Python

Python is used by:

- Huginn
- Heimdall
- Daily Video Game Releases
- Watchlist Release Monitor
- Vercel API endpoints

Python **3.11** is recommended.

## Installation

Clone the repository:

```bash
git clone https://github.com/Maria0696/script-station.git
cd script-station
```

### Ruby dependencies

```bash
bundle install
```

### Python dependencies

For development and testing:

```bash
pip install -r requirements-dev.txt
```

Runtime dependencies are defined in:

```text
requirements.txt
```

Development and testing dependencies are defined in:

```text
requirements-dev.txt
```

---

# Usage

## Interactive Script-Station

Start the Ruby interface with:

```bash
rake start_tool
```

You can also create a shell alias:

```bash
alias script-station='cd ~/workspace/script-station && rake start_tool'
```

Reload your shell configuration:

```bash
source ~/.zshrc
```

Then launch Script-Station with:

```bash
script-station
```

---

# Available Tools

## GitHub Support → Add Workflow

The Add Workflow utility can add the same GitHub Actions workflow to multiple repositories and automatically open pull requests.

From the interactive menu:

```text
git-support
└── Github Manager
    └── Add workflow
```

The utility can be configured interactively or with a YAML configuration file.

Example:

```yaml
org: my-org
github_token: ghp_xxx
repo_list_path: repos.txt
workflow_template_path: templates/workflows/update-readme-profile.yml
branch_suffix: ci
dry_run: true
```

Set:

```yaml
dry_run: false
```

to actually clone repositories, create branches, commit changes, push them, and open pull requests.

The GitHub token is masked in logs.

> Never commit a real configuration file containing a GitHub token.

---

# Telegram Bots

## Huginn

Huginn is the gaming assistant for Script-Station.

It supports commands such as:

```text
/watch
/watchlist
/next
/unwatch
/help
```

Huginn uses IGDB to search for games, retrieve platform information and release dates, and manage the game watchlist.

Main logic:

```text
core/huginn.py
```

---

## Heimdall

Heimdall monitors Script-Station workflows.

It can show the current status of:

```text
Daily Video Game Releases
Watchlist Release Monitor
Quality Checks
```

Available commands:

```text
/status
/help
```

Main logic:

```text
core/heimdall.py
```

---

# Video Game Automations

## Daily Video Game Releases

```text
scripts/video_game_releases.py
```

Checks IGDB for games released during the current day and sends the results to Telegram.

The script also calculates a popularity score and can highlight the most relevant releases.

It runs automatically through:

```text
.github/workflows/videogames.yml
```

Required secrets:

```text
IGDB_CLIENT_ID
IGDB_CLIENT_SECRET
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

---

## Watchlist Release Monitor

```text
scripts/watchlist_monitor.py
```

Monitors games stored in:

```text
data/watchlist.json
```

It checks IGDB for changes to release dates and platform information.

When a relevant change is detected, the monitor can send a Telegram notification and update the stored watchlist.

It runs through:

```text
.github/workflows/watchlist.yml
```

---

# API

The Python API is implemented with FastAPI.

Main entry point:

```text
api/index.py
```

It exposes endpoints for both Telegram bots and provides health checks for the deployed service.

The API routes Telegram updates to either Huginn or Heimdall.

---

# Testing

All tests live under a single root directory:

```text
tests/
├── ruby/
└── python/
```

Each language keeps its own test framework and configuration.

## Ruby Tests

Ruby tests use RSpec.

Run them with:

```bash
rake test
```

or directly:

```bash
bundle exec rspec -I tests/ruby tests/ruby
```

Run RuboCop with:

```bash
bundle exec rubocop
```

Ruby tests are located in:

```text
tests/ruby/
```

The Ruby suite uses SimpleCov for coverage.

The current coverage gate requires:

```text
Total coverage:      >= 90%
Coverage per file:   >= 80%
```

The HTML coverage report is generated under:

```text
coverage/
```

and uploaded by GitHub Actions as:

```text
coverage-report
```

---

## Python Tests

Python tests use pytest.

They are located in:

```text
tests/python/
```

Run them with:

```bash
pytest
```

Pytest configuration is stored in:

```text
pytest.ini
```

To run Python tests with coverage:

```bash
pytest \
  --cov=core \
  --cov=scripts \
  --cov=api \
  --cov-report=term-missing
```

External services such as GitHub, Telegram and IGDB should be mocked during tests so the test suite does not depend on real API calls or credentials.

Test environment variables are configured in:

```text
tests/python/conftest.py
```

---

# Quality Checks

GitHub Actions runs automated quality checks for pull requests and pushes to `master`.

Workflow:

```text
.github/workflows/quality-checks.yml
```

The current Ruby checks include:

```text
RuboCop
RSpec
SimpleCov
```

Python tests use the same `tests/` structure and will be integrated into the same Quality Checks workflow.

---

# Project Structure

```text
script-station/
├── .github/
│   └── workflows/
│       ├── quality-checks.yml
│       ├── videogames.yml
│       └── watchlist.yml
│
├── api/
│   └── index.py
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── github.py
│   ├── heimdall.py
│   ├── huginn.py
│   ├── igdb.py
│   └── telegram.py
│
├── data/
│   └── watchlist.json
│
├── lib/
│   └── ...
│
├── scripts/
│   ├── video_game_releases.py
│   └── watchlist_monitor.py
│
├── templates/
│   └── ...
│
├── tests/
│   ├── ruby/
│   │   ├── fixtures/
│   │   ├── lib/
│   │   │   ├── git-support/
│   │   │   └── installation-support/
│   │   ├── scanner_spec.rb
│   │   └── spec_helper.rb
│   │
│   └── python/
│       └── conftest.py
│
├── tty_menu/
│   └── ...
│
├── .gitignore
├── .rubocop.yml
├── Gemfile
├── Gemfile.lock
├── pytest.ini
├── Rakefile
├── README.md
├── requirements.txt
├── requirements-dev.txt
└── vercel.json
```

---

# Adding Ruby Tools

Ruby tools follow the existing Script-Station structure.

Create the interactive menu entry under:

```text
tty_menu/<functionality>-support/
```

and place the implementation under:

```text
lib/<functionality>-support/
```

Example:

```text
script-station/
├── lib/
│   └── <functionality>-support/
│       ├── <name>.rb
│       └── ...
│
└── tty_menu/
    └── <functionality>-support/
        ├── <name>.rb
        └── ...
```

Tests for the functionality should be added under:

```text
tests/ruby/
```

following the same structure where appropriate.

---

# About the Menu

Script-Station uses the `Step` class to manage the interactive menu.

Example:

```ruby
step do
  # Logic to present options to the user
end
```

## Backward Navigation

To support backward navigation, steps should be nested:

```ruby
step do
  # First level

  step do
    # Second level
  end
end
```

---

# Contributing

Contributions are welcome.

When adding or modifying functionality:

1. Keep the existing project structure.
2. Add or update tests.
3. Run the relevant test suite locally.
4. Run the linters.
5. Open a pull request against `master`.

All pull requests should pass the `Quality Checks` workflow before being merged.