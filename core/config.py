import os

# ============================================================
# TELEGRAM
# ============================================================

# Huginn - Videojuegos
HUGINN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

HUGINN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# Heimdall - Monitorización
HEIMDALL_BOT_TOKEN = os.getenv("TELEGRAM_HEIMDALL_BOT_TOKEN")

HEIMDALL_CHAT_ID = os.getenv("TELEGRAM_HEIMDALL_CHAT_ID")


# Secretos que Telegram envía en cada webhook
HUGINN_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

HEIMDALL_WEBHOOK_SECRET = os.getenv("TELEGRAM_HEIMDALL_WEBHOOK_SECRET")


# ============================================================
# IGDB
# ============================================================

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")

IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")


# ============================================================
# GITHUB
# ============================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_REPO = "Maria0696/script-station"

GITHUB_BRANCH = "master"

WATCHLIST_PATH = "data/watchlist.json"

# Estado de los juegos que ya han salido en todas sus plataformas
RELEASED_STATUS = "released"


# ============================================================
# CRON
# ============================================================

# Vercel lo envía como "Authorization: Bearer ..."
CRON_SECRET = os.getenv("CRON_SECRET")

# Workflows lanzados por el cron diario de Vercel
# y vigilados por el watchdog diario: archivo -> etiqueta
DAILY_WORKFLOWS = {
    "videogames.yml": "🎮 Daily Releases",
    "watchlist.yml": "👀 Watchlist Monitor",
}


# ============================================================
# PLATAFORMAS
# ============================================================

PLATFORM_LABELS = {
    167: "🔵 PS5",
    508: "🔴 Switch 2",
    6: "💻 PC",
    169: "🟢 Xbox Series",
    48: "🔵 PS4",
    49: "🟢 Xbox One",
    130: "🔴 Switch",
    390: "🥽 PS VR2",
    471: "🥽 Meta Quest",  # Meta Quest 3
    386: "🥽 Meta Quest",  # Meta Quest 2
    163: "🥽 SteamVR",
}


PLATFORM_ORDER = [
    167,  # PS5
    508,  # Switch 2
    6,  # PC
    169,  # Xbox Series
    48,  # PS4
    49,  # Xbox One
    130,  # Switch
    390,  # PS VR2
    471,  # Meta Quest 3
    386,  # Meta Quest 2
    163,  # SteamVR
]


VALID_REGIONS = {"europe", "worldwide"}


# ============================================================
# HEIMDALL
# ============================================================

WORKFLOWS = {
    "Daily Video Game Releases": "🎮 Daily Releases",
    "Watchlist Release Monitor": "👀 Watchlist Monitor",
    "Quality Checks": "🧪 Quality Checks",
    "Daily Watchdog": "⏰ Daily Watchdog",
}
