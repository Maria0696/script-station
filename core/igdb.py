import json
from datetime import UTC, date, datetime
from urllib import parse, request

from core.config import (
    IGDB_CLIENT_ID,
    IGDB_CLIENT_SECRET,
    PLATFORM_LABELS,
    PLATFORM_ORDER,
    VALID_REGIONS,
)


def get_igdb_token():
    # Obtiene un token temporal de Twitch
    params = parse.urlencode(
        {
            "client_id": IGDB_CLIENT_ID,
            "client_secret": IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }
    )

    url = (
        "https://id.twitch.tv/oauth2/token?"
        + params
    )

    req = request.Request(
        url,
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(
            response.read()
        )["access_token"]


def igdb_request(
    token,
    endpoint,
    query,
):
    # Ejecuta una consulta a IGDB
    req = request.Request(
        f"https://api.igdb.com/v4/{endpoint}",
        data=query.encode("utf-8"),
        headers={
            "Client-ID": IGDB_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


def search_igdb_games(game_name):
    # Busca juegos por nombre
    token = get_igdb_token()

    safe_name = (
        game_name
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    query = f"""
    search "{safe_name}";

    fields
        id,
        name,
        first_release_date;

    limit 5;
    """

    return igdb_request(
        token,
        "games",
        query,
    )


def get_igdb_game(game_id):
    # Obtiene un juego exacto
    token = get_igdb_token()

    query = f"""
    fields
        id,
        name,
        first_release_date,
        platforms;

    where id = {game_id};

    limit 1;
    """

    games = igdb_request(
        token,
        "games",
        query,
    )

    if not games:
        return None

    return games[0]


def get_platform_release_dates(game_id):
    # Obtiene las fechas por plataforma
    token = get_igdb_token()

    platform_ids = ",".join(
        str(platform_id)
        for platform_id in PLATFORM_ORDER
    )

    query = f"""
    fields
        platform,
        date,
        release_region.region;

    where game = {game_id}
        & platform = ({platform_ids});

    limit 500;

    sort date asc;
    """

    releases = igdb_request(
        token,
        "release_dates",
        query,
    )

    release_dates = {}

    for release in releases:
        platform_id = release.get("platform")
        timestamp = release.get("date")
        region = release.get("release_region")

        if platform_id not in PLATFORM_LABELS:
            continue

        # Solo Europa, Worldwide o sin región
        if isinstance(region, dict):
            region_name = (
                region
                .get("region", "")
                .lower()
            )

            if (
                region_name
                and region_name not in VALID_REGIONS
            ):
                continue

        release_date = format_release_date(
            timestamp
        )

        if not release_date:
            continue

        # Conserva la primera fecha válida
        if platform_id not in release_dates:
            release_dates[
                platform_id
            ] = release_date

    return release_dates


def format_release_date(timestamp):
    # Convierte timestamp a YYYY-MM-DD
    if not timestamp:
        return None

    return datetime.fromtimestamp(
        timestamp,
        tz=UTC,
    ).date().isoformat()


def display_release_date(date_string):
    # Convierte YYYY-MM-DD a DD-MM-YYYY
    if not date_string:
        return "Sin fecha"

    return date.fromisoformat(
        date_string
    ).strftime(
        "%d-%m-%Y"
    )


def build_platform_data(game):
    # Une plataformas con sus fechas
    release_dates = (
        get_platform_release_dates(
            game["id"]
        )
    )

    platform_ids = set(
        game.get(
            "platforms",
            [],
        )
    )

    platform_ids.update(
        release_dates.keys()
    )

    platforms = []
    label_indexes = {}

    for platform_id in PLATFORM_ORDER:
        if platform_id not in platform_ids:
            continue

        label = PLATFORM_LABELS[
            platform_id
        ]

        release_date = release_dates.get(
            platform_id
        )

        # Agrupa Meta Quest 2 y 3
        if label in label_indexes:
            index = label_indexes[label]

            current_date = platforms[
                index
            ].get("release_date")

            if (
                current_date is None
                and release_date
            ):
                platforms[index][
                    "release_date"
                ] = release_date

            continue

        label_indexes[label] = len(
            platforms
        )

        platforms.append(
            {
                "id": platform_id,
                "label": label,
                "release_date": release_date,
            }
        )

    return platforms
