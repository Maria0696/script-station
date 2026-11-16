import calendar
import time
from datetime import UTC, date, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from core.config import (
    IGDB_CLIENT_ID,
    IGDB_CLIENT_SECRET,
    PLATFORM_LABELS,
    PLATFORM_ORDER,
    VALID_REGIONS,
)

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"  # noqa: S105
IGDB_API_URL = "https://api.igdb.com/v4"

# Renueva el token un poco antes de que caduque
TOKEN_EXPIRY_MARGIN = 60

# Precisión de cada date_format de IGDB. "TBD" no es una fecha.
# Para mes, trimestre o año, IGDB usa el último día del periodo
DATE_PRECISIONS = {
    "YYYYMMDD": "day",
    "YYYYMM": "month",
    "YYYYQ1": "quarter",
    "YYYYQ2": "quarter",
    "YYYYQ3": "quarter",
    "YYYYQ4": "quarter",
    "YYYY": "year",
}

# De más a menos concreta
PRECISION_ORDER = ("day", "month", "quarter", "year")

MONTH_NAMES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

# Token de Twitch compartido mientras siga vigente
_token_cache = {"access_token": None, "expires_at": 0.0}


def create_session():
    # Reintenta límites de uso (429) y errores temporales (5xx).
    # Las consultas a IGDB son de solo lectura, así que repetir
    # un POST es seguro. Esperas: 0.5 s, 1 s, 2 s o Retry-After
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        respect_retry_after_header=True,
        # Devuelve la última respuesta para incluirla en el error
        raise_on_status=False,
    )

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))

    return session


session = create_session()


# ============================================================
# PETICIONES HTTP
# ============================================================


def clear_token_cache():
    # Olvida el token guardado
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0.0


def get_igdb_token():
    # Reutiliza el token de Twitch hasta que caduca
    now = time.monotonic()

    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    response = session.post(
        TWITCH_TOKEN_URL,
        params={
            "client_id": IGDB_CLIENT_ID,
            "client_secret": IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 0) - TOKEN_EXPIRY_MARGIN

    return data["access_token"]


def igdb_request(endpoint, query):
    # Ejecuta una consulta a IGDB
    response = session.post(
        f"{IGDB_API_URL}/{endpoint}",
        headers={
            "Client-ID": IGDB_CLIENT_ID,
            "Authorization": f"Bearer {get_igdb_token()}",
            "Accept": "application/json",
        },
        # IGDB espera UTF-8 (nombres con acentos, kanji...)
        data=query.encode("utf-8"),
        timeout=30,
    )

    if not response.ok:
        raise requests.HTTPError(
            f"IGDB {endpoint} failed: "
            f"HTTP {response.status_code}: "
            f"{response.text[:500]}",
            response=response,
        )

    return response.json()


def platform_filter():
    # Plataformas soportadas para las consultas
    return ",".join(str(platform_id) for platform_id in PLATFORM_ORDER)


def is_valid_region(release):
    # Solo Europa, Worldwide o sin región
    region = release.get("release_region")

    if not isinstance(region, dict):
        return True

    region_name = (region.get("region") or "").lower()

    return not region_name or region_name in VALID_REGIONS


# ============================================================
# JUEGOS
# ============================================================


def search_igdb_games(game_name):
    # Busca juegos por nombre
    safe_name = game_name.replace("\\", "\\\\").replace('"', '\\"')

    query = f"""
    search "{safe_name}";

    fields
        id,
        name,
        first_release_date;

    limit 5;
    """

    return igdb_request("games", query)


def get_igdb_games(game_ids):
    # Obtiene varios juegos indexados por ID
    if not game_ids:
        return {}

    ids = ",".join(str(game_id) for game_id in game_ids)

    query = f"""
    fields
        id,
        name,
        first_release_date,
        platforms,
        aggregated_rating,
        aggregated_rating_count;

    where id = ({ids});

    limit 500;
    """

    return {game["id"]: game for game in igdb_request("games", query)}


def get_igdb_game(game_id):
    # Obtiene un juego exacto
    return get_igdb_games([game_id]).get(game_id)


# ============================================================
# FECHAS DE LANZAMIENTO
# ============================================================


def get_release_dates(game_ids):
    # Primera fecha válida por juego y plataforma:
    # {game_id: {platform_id: {"date": "YYYY-MM-DD", "precision": "day"}}}
    if not game_ids:
        return {}

    ids = ",".join(str(game_id) for game_id in game_ids)

    query = f"""
    fields
        game,
        platform,
        date,
        date_format.format,
        release_region.region;

    where game = ({ids})
        & platform = ({platform_filter()});

    limit 500;

    sort date asc;
    """

    release_dates = {}

    for release in igdb_request("release_dates", query):
        game_id = release.get("game")
        platform_id = release.get("platform")

        if isinstance(game_id, dict):
            game_id = game_id.get("id")

        if platform_id not in PLATFORM_LABELS or not is_valid_region(release):
            continue

        release_date = format_release_date(release.get("date"))
        precision = get_date_precision(release)

        if not release_date or not precision:
            continue

        # Conserva la primera fecha válida
        release_dates.setdefault(game_id, {}).setdefault(
            platform_id, {"date": release_date, "precision": precision}
        )

    return release_dates


def get_platform_release_dates(game_id):
    # Fechas por plataforma de un solo juego
    return get_release_dates([game_id]).get(game_id, {})


def get_releases_between(start_timestamp, end_timestamp):
    # Lanzamientos en plataformas soportadas en un intervalo
    query = f"""
    fields
        game.id,
        game.name,
        platform,
        release_region.region,
        date,
        human;

    where date >= {start_timestamp}
        & date < {end_timestamp}
        & platform = ({platform_filter()});

    limit 500;

    sort date asc;
    """

    return igdb_request("release_dates", query)


def get_popularity_primitives(game_ids, popularity_types):
    # Métricas de popularidad de varios juegos
    if not game_ids:
        return []

    ids = ",".join(str(game_id) for game_id in game_ids)

    types = ",".join(str(popularity_type) for popularity_type in popularity_types)

    query = f"""
    fields
        game_id,
        popularity_type,
        value;

    where game_id = ({ids})
        & popularity_type = ({types});

    limit 500;
    """

    return igdb_request("popularity_primitives", query)


def format_release_date(timestamp):
    # Convierte timestamp a YYYY-MM-DD
    if not timestamp:
        return None

    return datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()


def get_date_precision(release):
    # Precisión de una fecha de IGDB; None si está por determinar.
    # Sin date_format se asume día, como hacía IGDB antes
    date_format = release.get("date_format")

    if not isinstance(date_format, dict):
        return "day"

    return DATE_PRECISIONS.get(date_format.get("format"))


def display_release_date(date_string, precision="day"):
    # Muestra la fecha según su precisión:
    # 15-03-2027, Marzo 2027, T1 2027 o 2027
    if not date_string:
        return "Sin fecha"

    value = date.fromisoformat(date_string)

    if precision == "year":
        return str(value.year)

    if precision == "quarter":
        return f"T{(value.month - 1) // 3 + 1} {value.year}"

    if precision == "month":
        return f"{MONTH_NAMES[value.month - 1].capitalize()} {value.year}"

    return value.strftime("%d-%m-%Y")


def get_platform_precision(platform):
    # Precisión guardada; los datos antiguos eran siempre por día
    return platform.get("date_precision") or "day"


def display_platform_date(platform):
    # Fecha visible de una plataforma de la watchlist
    return display_release_date(
        platform.get("release_date"), get_platform_precision(platform)
    )


def release_period(date_string, precision="day"):
    # Primer y último día que abarca una fecha imprecisa
    value = date.fromisoformat(date_string)

    if precision == "year":
        return date(value.year, 1, 1), date(value.year, 12, 31)

    if precision == "quarter":
        first_month = (value.month - 1) // 3 * 3 + 1
        last_month = first_month + 2
        last_day = calendar.monthrange(value.year, last_month)[1]

        return date(value.year, first_month, 1), date(value.year, last_month, last_day)

    if precision == "month":
        last_day = calendar.monthrange(value.year, value.month)[1]

        return date(value.year, value.month, 1), date(value.year, value.month, last_day)

    return value, value


def is_more_precise(precision, other):
    # True si precision concreta más que other
    return PRECISION_ORDER.index(precision) < PRECISION_ORDER.index(other)


# ============================================================
# PLATAFORMAS
# ============================================================


def build_platform_data(game, release_dates=None):
    # Une plataformas con sus fechas.
    # Sin release_dates, las consulta a IGDB
    if release_dates is None:
        release_dates = get_platform_release_dates(game["id"])

    platform_ids = set(game.get("platforms", []))

    platform_ids.update(release_dates.keys())

    platforms = []
    label_indexes = {}

    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[platform_id]

        release = release_dates.get(platform_id) or {}

        release_date = release.get("date")
        precision = release.get("precision")

        # Agrupa Meta Quest 2 y 3
        if label in label_indexes:
            platform = platforms[label_indexes[label]]

            if platform["release_date"] is None and release_date:
                platform["release_date"] = release_date
                platform["date_precision"] = precision

            continue

        label_indexes[label] = len(platforms)

        platforms.append(
            {
                "id": platform_id,
                "label": label,
                "release_date": release_date,
                "date_precision": precision,
            }
        )

    return platforms
