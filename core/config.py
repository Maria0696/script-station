import os

# Configuración compartida. Los valores sensibles llegan por variables de
# entorno: secretos de GitHub Actions, variables de Vercel o un .env local.
# Se leen al importar, así que el .env debe cargarse antes de importar core.

# ============================================================
# TELEGRAM
# ============================================================

# Huginn (videojuegos). Las variables no llevan "HUGINN" porque Huginn
# fue el primer bot; renombrarlas obligaría a cambiar todos los secretos
HUGINN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Único chat autorizado: los bots ignoran cualquier otro
HUGINN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Heimdall (monitorización de workflows)
HEIMDALL_BOT_TOKEN = os.getenv("TELEGRAM_HEIMDALL_BOT_TOKEN")

HEIMDALL_CHAT_ID = os.getenv("TELEGRAM_HEIMDALL_CHAT_ID")

# secret_token registrado con setWebhook; Telegram lo envía en cada update
HUGINN_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

HEIMDALL_WEBHOOK_SECRET = os.getenv("TELEGRAM_HEIMDALL_WEBHOOK_SECRET")


# ============================================================
# IGDB
# ============================================================

# IGDB se autentica con una aplicación de Twitch
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")

IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")


# ============================================================
# GITHUB
# ============================================================

# En Vercel y en el monitor es un token de admin: master exige PR y solo
# los admins pueden saltarse esa regla al guardar la watchlist
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_REPO = "Maria0696/script-station"

GITHUB_BRANCH = "master"

# La watchlist se guarda en el propio repositorio, vía API de GitHub
WATCHLIST_PATH = "data/watchlist.json"

# Juego que ya ha salido en todas sus plataformas con fecha
RELEASED_STATUS = "released"


# ============================================================
# CRON
# ============================================================

CRON_SECRET = os.getenv("CRON_SECRET")

# Workflows que el cron de Vercel lanza cada día y que el watchdog vigila.
# Son también los únicos que Heimdall permite lanzar desde un botón
DAILY_WORKFLOWS = {
    "videogames.yml": "🎮 Daily Releases",
    "watchlist.yml": "👀 Watchlist Monitor",
}


# ============================================================
# PLATAFORMAS
# ============================================================

# IDs de plataforma de IGDB. Quest 2 y 3 comparten etiqueta y se agrupan
PLATFORM_LABELS = {
    167: "🔵 PS5",
    508: "🔴 Switch 2",
    6: "💻 PC",
    169: "🟢 Xbox Series",
    48: "🔵 PS4",
    49: "🟢 Xbox One",
    130: "🔴 Switch",
    390: "🥽 PS VR2",
    471: "🥽 Meta Quest",
    386: "🥽 Meta Quest",
    163: "🥽 SteamVR",
}

# Orden en el que se muestran las plataformas
PLATFORM_ORDER = [167, 508, 6, 169, 48, 49, 130, 390, 471, 386, 163]

# Regiones de lanzamiento que interesan; las fechas sin región también valen
VALID_REGIONS = {"europe", "worldwide"}


# ============================================================
# HEIMDALL
# ============================================================

# Workflows que muestra /status. La clave debe coincidir con el "name:"
# del workflow, que es lo que devuelve la API de GitHub
WORKFLOWS = {
    "Daily Video Game Releases": "🎮 Daily Releases",
    "Watchlist Release Monitor": "👀 Watchlist Monitor",
    "Quality Checks": "🧪 Quality Checks",
    "Daily Watchdog": "⏰ Daily Watchdog",
}
