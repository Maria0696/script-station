# Script Station

[![Quality Checks](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml/badge.svg)](https://github.com/Maria0696/script-station/actions/workflows/quality-checks.yml)

Script Station is a Python automation and monitoring toolkit.

It combines an interactive terminal interface, GitHub automation utilities, Telegram bots, video game release tracking, watchlist monitoring, scheduled GitHub Actions workflows and centralized notifications.

---

## Features

- **Interactive Python CLI** with guided terminal menus.
- **Direct CLI commands** for automation without opening the interactive menu.
- **GitHub automation** for repetitive repository operations.
- **Huginn** Telegram bot for video game features.
- **Heimdall** Telegram bot for workflow monitoring.
- **IGDB integration** for game information and release dates.
- **Watchlist monitoring** for release date and platform changes.
- **Event-based NotificationService** for centralized notification routing.
- **Scheduled GitHub Actions** for automated reports and monitoring.
- **FastAPI webhooks** for Telegram.
- **Python-only test and quality pipeline** using pytest, coverage and Ruff.

---

# Requirements

Python **3.11 or newer**.

Check your version with:

```bash
python --version
```

On Windows:

```powershell
py --version
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Maria0696/script-station.git
cd script-station
```

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

On Windows:

```powershell
py -m pip install -r requirements-dev.txt
```

Install Script Station in editable mode:

```bash
python -m pip install -e .
```

On Windows:

```powershell
py -m pip install -e .
```

This installs the global project command:

```text
script-station
```

Editable mode means changes to the source code are immediately reflected without reinstalling the project.

---

# Environment Variables

Local environment variables can be stored in:

```text
.env
```

The `.env` file must never be committed.

Depending on the functionality being used, Script Station can require the following variables:

```text
IGDB_CLIENT_ID
IGDB_CLIENT_SECRET

TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

TELEGRAM_HEIMDALL_BOT_TOKEN
TELEGRAM_HEIMDALL_CHAT_ID

GITHUB_TOKEN
```

## IGDB

Used by video game search, release reports and watchlist monitoring:

```text
IGDB_CLIENT_ID
IGDB_CLIENT_SECRET
```

## Huginn

Used by the gaming Telegram bot:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

## Heimdall

Used by the workflow monitoring Telegram bot:

```text
TELEGRAM_HEIMDALL_BOT_TOKEN
TELEGRAM_HEIMDALL_CHAT_ID
```

## GitHub

Used for GitHub API operations:

```text
GITHUB_TOKEN
```

The token should only receive the permissions required by the operations you intend to use.

For the current GitHub integrations this can include:

```text
Actions: Read and write
Contents: Read and write
```

Never commit a real token.

---

# Usage

## Interactive Menu

Launch Script Station with:

```bash
script-station
```

or:

```bash
script-station menu
```

The interactive Python menu provides access to:

```text
Script Station
│
├── Git Support
│   └── Add workflow
│
├── Installation Support
│   └── Package manager
│
├── Video Games
│   ├── Video Game Releases
│   └── Watchlist Monitor
│
├── Heimdall
│   ├── Status
│   └── Failures
│
└── Exit
```

The menu is implemented entirely in Python.

---

# CLI Commands

Script Station can also execute tools directly without opening the interactive menu.

Show available commands:

```bash
script-station --help
```

---

## Video Game Releases

```bash
script-station releases
```

Runs the daily video game release report.

The command uses IGDB to retrieve games released during the current day and sends the report through Huginn.

Equivalent Python module:

```bash
python -m scripts.video_game_releases
```

---

## Watchlist Monitor

```bash
script-station watchlist
```

Checks the stored game watchlist for release date and platform changes.

Equivalent Python module:

```bash
python -m scripts.watchlist_monitor
```

---

## Heimdall Status

```bash
script-station heimdall status
```

Displays the latest status of Script Station workflows directly in the terminal.

Current monitored workflows include:

```text
Daily Video Game Releases
Watchlist Release Monitor
Quality Checks
```

---

## Heimdall Failures

```bash
script-station heimdall failures
```

Displays currently failed workflows.

---

## GitHub Add Workflow

```bash
script-station github add-workflow
```

Adds the same GitHub Actions workflow to multiple repositories and automatically opens pull requests.

---

## Package Manager

```bash
script-station install package-manager
```

Provides installation support for:

```text
Windows → Chocolatey
macOS   → Homebrew
Linux   → Flatpak
```

The selected installer is only executed after confirmation.

---

## Notifications

Workflow failure notifications can be triggered through:

```bash
script-station notify workflow-failed
```

This command is mainly intended for GitHub Actions, where the required GitHub workflow environment variables are already available.

---

# GitHub Automation

## Add Workflow

The Add Workflow utility automates adding the same workflow file to multiple repositories.

It can:

```text
1. Read a list of repositories.
2. Detect each repository's default branch.
3. Create a new branch through the GitHub API.
4. Upload the workflow file.
5. Commit the workflow through GitHub.
6. Open a pull request automatically.
```

The Python implementation communicates directly with the GitHub API.

It does not need to clone every target repository locally.

---

## Configuration File

Add Workflow can be configured using YAML.

Example:

```yaml
org: my-org
github_token_env: GITHUB_TOKEN
repo_list_path: repos.txt
workflow_template_path: templates/workflows/update-readme-profile.yml
branch_suffix: ci
dry_run: true
```

The token is referenced through:

```yaml
github_token_env: GITHUB_TOKEN
```

instead of being stored directly in the YAML file.

Recommended local configuration:

```env
GITHUB_TOKEN=your_token_here
```

---

## Dry Run

Use:

```yaml
dry_run: true
```

to preview what would happen without modifying repositories.

A dry run shows operations such as:

```text
[DRY RUN] Would update organization/repository
[DRY RUN] Would create branch ...
[DRY RUN] Would add .github/workflows/...
[DRY RUN] Would commit and open a pull request
```

Set:

```yaml
dry_run: false
```

to perform the real GitHub operations.

---

# Telegram Bots

Script Station contains two Telegram bots with different responsibilities.

---

## Huginn

Huginn is the gaming assistant.

Main logic:

```text
core/huginn.py
```

It integrates with IGDB and the game watchlist.

Available commands include:

```text
/watch
/watchlist
/next
/unwatch
/help
```

Huginn can:

- Search for games.
- Retrieve platform information.
- Retrieve release dates.
- Add games to the watchlist.
- Remove games from the watchlist.
- Show watched games.
- Show upcoming releases.

---

## Heimdall

Heimdall monitors Script Station infrastructure and GitHub Actions workflows.

Main logic:

```text
core/heimdall.py
```

Available commands include:

```text
/status
/failures
/help
```

Heimdall can:

- Show workflow status.
- Detect active workflow failures.
- Display workflow branches and execution times.
- Link directly to GitHub Actions runs.
- Re-run failed workflow jobs through Telegram buttons.

---

# Notification Service

Notifications are centralized through:

```text
core/notifications.py
```

Consumers do not need to know which Telegram bot should receive a specific event.

Instead, they emit notification events.

Current routing:

```text
workflow.failed
      ↓
NotificationService
      ↓
Heimdall
```

and:

```text
game.release_changed
      ↓
NotificationService
      ↓
Huginn
```

Conceptually:

```python
notifications.emit(
    "workflow.failed",
    message,
)
```

instead of:

```python
notifications.heimdall(
    message,
)
```

This keeps notification producers decoupled from notification channels.

---

# Video Game Automations

## Daily Video Game Releases

Main script:

```text
scripts/video_game_releases.py
```

Workflow:

```text
.github/workflows/videogames.yml
```

The automation:

- Authenticates with IGDB.
- Retrieves releases for the current day.
- Filters and processes release information.
- Calculates release relevance.
- Builds a Telegram report.
- Sends the result through Huginn.

Required variables:

```text
IGDB_CLIENT_ID
IGDB_CLIENT_SECRET
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

---

## Watchlist Release Monitor

Main script:

```text
scripts/watchlist_monitor.py
```

Watchlist data:

```text
data/watchlist.json
```

Workflow:

```text
.github/workflows/watchlist.yml
```

The monitor:

- Loads watched games.
- Queries current IGDB information.
- Retrieves platform-specific release dates.
- Detects delays.
- Detects release advances.
- Detects newly announced dates.
- Detects removed dates.
- Detects platform changes.
- Updates the stored watchlist.
- Emits `game.release_changed` notifications when relevant.

---

# API

The web API is implemented with FastAPI.

Main entry point:

```text
api/index.py
```

It handles Telegram webhook requests for:

```text
Huginn
Heimdall
```

Deployment configuration:

```text
vercel.json
```

---

# Core Modules

Shared application logic lives in:

```text
core/
```

Current modules include:

```text
core/
├── config.py
├── github.py
├── heimdall.py
├── huginn.py
├── igdb.py
├── notifications.py
└── telegram.py
```

## `config.py`

Shared application configuration.

## `github.py`

GitHub API operations used by the bots and monitoring tools.

## `heimdall.py`

Workflow monitoring and Heimdall Telegram behavior.

## `huginn.py`

Gaming assistant and watchlist Telegram behavior.

## `igdb.py`

Shared IGDB integration.

## `notifications.py`

Event-based notification routing.

## `telegram.py`

Low-level Telegram transport.

---

# Scripts

Executable automation modules live under:

```text
scripts/
```

Current tools include:

```text
scripts/
├── add_workflow.py
├── notify.py
├── package_manager.py
├── video_game_releases.py
└── watchlist_monitor.py
```

The `script-station` CLI provides a common interface over these tools.

---

# Testing

Script Station uses **pytest**.

Tests are stored in:

```text
tests/python/
```

Run the complete suite:

```bash
python -m pytest
```

On Windows:

```powershell
py -m pytest
```

Run a specific file:

```bash
python -m pytest tests/python/test_cli.py -vv
```

---

# Coverage

Run Python tests with coverage:

```bash
python -m pytest \
  --cov=core \
  --cov=api \
  --cov=scripts \
  --cov=station_cli \
  --cov-report=term-missing \
  --cov-fail-under=90
```

PowerShell:

```powershell
py -m pytest `
  --cov=core `
  --cov=api `
  --cov=scripts `
  --cov=station_cli `
  --cov-report=term-missing `
  --cov-fail-under=90
```

The project requires at least:

```text
90% Python coverage
```

External services such as GitHub, Telegram and IGDB are mocked during tests.

Tests must not depend on real credentials or external API calls.

---

# Ruff

Ruff is used for Python linting.

Run:

```bash
python -m ruff check api core scripts station_cli.py tests/python
```

On Windows:

```powershell
py -m ruff check api core scripts station_cli.py tests/python
```

A successful result should be:

```text
All checks passed!
```

---

# Quality Checks

GitHub Actions runs automated checks for pull requests and pushes to `master`.

Workflow:

```text
.github/workflows/quality-checks.yml
```

Current checks include:

```text
Ruff
Pytest
Python coverage
CLI installation
CLI --help smoke test
```

The workflow installs Script Station using:

```bash
python -m pip install -e .
```

and verifies:

```bash
script-station --help
```

All pull requests should have green Quality Checks before being merged.

---

# Automated Workflows

Script Station currently contains:

```text
.github/workflows/
├── quality-checks.yml
├── videogames.yml
└── watchlist.yml
```

## Quality Checks

Runs code quality and tests.

## Daily Video Game Releases

Runs the scheduled daily release report.

## Watchlist Release Monitor

Checks the watchlist for release changes.

Workflow failures can emit:

```text
workflow.failed
```

which is routed automatically to Heimdall.

---

# Dependency Management

Runtime dependencies are defined in:

```text
requirements.txt
```

Development dependencies are defined in:

```text
requirements-dev.txt
```

Python project metadata and the CLI entry point are defined in:

```text
pyproject.toml
```

Dependabot monitors:

```text
Python dependencies
GitHub Actions
```

---

# Project Structure

```text
script-station/
│
├── .github/
│   ├── dependabot.yml
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
│   ├── notifications.py
│   └── telegram.py
│
├── data/
│   └── watchlist.json
│
├── scripts/
│   ├── __init__.py
│   ├── add_workflow.py
│   ├── notify.py
│   ├── package_manager.py
│   ├── video_game_releases.py
│   └── watchlist_monitor.py
│
├── templates/
│   ├── configs/
│   │   └── add-workflow.yml
│   └── workflows/
│       └── update-readme-profile.yml
│
├── tests/
│   └── python/
│       ├── conftest.py
│       ├── test_add_workflow.py
│       ├── test_api.py
│       ├── test_cli.py
│       ├── test_github.py
│       ├── test_heimdall.py
│       ├── test_huginn.py
│       ├── test_igdb.py
│       ├── test_notifications.py
│       ├── test_notify.py
│       ├── test_package_manager.py
│       ├── test_telegram.py
│       ├── test_video_game_releases.py
│       └── test_watchlist_monitor.py
│
├── .gitignore
├── pyproject.toml
├── pytest.ini
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── station_cli.py
└── vercel.json
```

---

# Generated Local Files

Some directories can appear locally while developing but are not part of the application source code:

```text
__pycache__/
.pytest_cache/
.ruff_cache/
coverage-python/
*.egg-info/
```

They are generated automatically and ignored by Git.

---

# Development Workflow

Recommended workflow for changes:

```text
1. Create a branch.
2. Implement the change.
3. Add or update tests.
4. Run Ruff.
5. Run pytest.
6. Check coverage.
7. Push the branch.
8. Open a pull request.
9. Wait for Quality Checks.
10. Merge when everything is green.
```

Before committing:

```bash
python -m ruff check api core scripts station_cli.py tests/python
python -m pytest
git diff --check
```

On Windows:

```powershell
py -m ruff check api core scripts station_cli.py tests/python
py -m pytest
git diff --check
```

---

# Security

- Never commit `.env`.
- Never commit GitHub tokens.
- Never commit Telegram bot tokens.
- Never put production secrets inside YAML templates.
- Use environment variables for credentials.
- Mock external services during tests.
- Use the minimum permissions required for GitHub tokens.

Example:

```yaml
github_token_env: GITHUB_TOKEN
```

instead of:

```yaml
github_token: real-secret-token
```

---

# Contributing

Contributions should follow the existing Python architecture.

When adding functionality:

1. Keep business logic outside CLI routing where possible.
2. Reuse shared modules from `core/`.
3. Add executable automation under `scripts/` when appropriate.
4. Add tests under `tests/python/`.
5. Keep external API calls mockable.
6. Run Ruff and pytest locally.
7. Open a pull request against `master`.
8. Merge only when Quality Checks are green.

---

# License

No license has been defined yet.
