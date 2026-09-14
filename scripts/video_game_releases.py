import os
from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

import requests

from core.notifications import (
    notifications,
)

# Credenciales de IGDB
CLIENT_ID = os.environ[
    "IGDB_CLIENT_ID"
]

CLIENT_SECRET = os.environ[
    "IGDB_CLIENT_SECRET"
]


# Zona horaria usada para definir "hoy"
MADRID_TZ = ZoneInfo(
    "Europe/Madrid"
)


# Muestra logs detallados de popularidad
DEBUG = (
    os.getenv(
        "DEBUG",
        "false",
    ).lower()
    == "true"
)


# IDs de plataformas y nombre mostrado
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
PLATFORM_ORDER = [
    167,
    508,
    6,
    169,
    48,
    49,
    130,
    390,
    471,
    386,
    163,
]


# Regiones válidas
VALID_REGIONS = {
    "europe",
    "worldwide",
}


# Tipos de popularidad de IGDB
POPULARITY_VISITS = 1
POPULARITY_WANT_TO_PLAY = 2


# Peso de cada métrica
VISITS_WEIGHT = 0.4
WANT_TO_PLAY_WEIGHT = 0.6


# Reglas para marcar juegos con ⭐
FEATURED_SCORE_MIN = 0.00002
FEATURED_RELATIVE_THRESHOLD = 0.75
MAX_FEATURED_GAMES = 3


# Solo para mostrar scores legibles en logs
LOG_SCORE_MULTIPLIER = (
    1_000_000
)


# Margen respecto al límite de Telegram
MAX_TELEGRAM_LENGTH = 3900


def get_access_token():
    # Obtiene token temporal de Twitch para usar IGDB
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id":
                CLIENT_ID,
            "client_secret":
                CLIENT_SECRET,
            "grant_type":
                "client_credentials",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()[
        "access_token"
    ]


def get_igdb_headers(token):
    # Cabeceras necesarias para consultar IGDB
    return {
        "Client-ID":
            CLIENT_ID,
        "Authorization":
            f"Bearer {token}",
        "Accept":
            "application/json",
    }


def get_releases_today(token):
    # Fecha actual según Madrid
    today = datetime.now(
        MADRID_TZ
    ).date()

    start_datetime = datetime(
        today.year,
        today.month,
        today.day,
        0,
        0,
        0,
        tzinfo=MADRID_TZ,
    )

    end_datetime = (
        start_datetime
        + timedelta(days=1)
    )

    start_ts = int(
        start_datetime.timestamp()
    )

    end_ts = int(
        end_datetime.timestamp()
    )

    platform_ids = ",".join(
        str(platform_id)
        for platform_id
        in PLATFORM_ORDER
    )

    query = f"""
    fields
        game.id,
        game.name,
        platform,
        release_region.region,
        date,
        human;

    where date >= {start_ts}
        & date < {end_ts}
        & platform = ({platform_ids});

    limit 500;
    sort date asc;
    """

    response = requests.post(
        (
            "https://api.igdb.com/v4/"
            "release_dates"
        ),
        headers=get_igdb_headers(
            token
        ),
        data=query,
        timeout=30,
    )

    if not response.ok:
        print(
            "IGDB releases error: "
            f"{response.status_code}"
        )

        print(
            response.text
        )

    response.raise_for_status()

    releases = response.json()

    print(
        "IGDB releases received: "
        f"{len(releases)}"
    )

    return filter_and_group_releases(
        releases
    )


def filter_and_group_releases(
    releases,
):
    games = {}

    for release in releases:
        region = release.get(
            "release_region"
        )

        if isinstance(
            region,
            dict,
        ):
            region_name = (
                region.get(
                    "region",
                    "",
                )
                .lower()
            )

            if (
                region_name
                and region_name
                not in VALID_REGIONS
            ):
                continue

        game = release.get(
            "game"
        )

        if not isinstance(
            game,
            dict,
        ):
            continue

        game_id = game.get(
            "id"
        )

        game_name = game.get(
            "name"
        )

        platform_id = (
            release.get(
                "platform"
            )
        )

        if (
            not game_id
            or not game_name
            or platform_id
            not in PLATFORM_LABELS
        ):
            continue

        if game_id not in games:
            games[
                game_id
            ] = {
                "id":
                    game_id,
                "name":
                    game_name,
                "platforms":
                    set(),
                "visits":
                    0.0,
                "want_to_play":
                    0.0,
                "popularity_score":
                    0.0,
                "featured":
                    False,
            }

        games[
            game_id
        ][
            "platforms"
        ].add(
            platform_id
        )

    print(
        "Games to send: "
        f"{len(games)}"
    )

    return list(
        games.values()
    )


def add_popularity_data(
    token,
    games,
):
    # No consulta popularidad si no hay juegos
    if not games:
        return games

    game_ids = ",".join(
        str(game["id"])
        for game in games
    )

    query = f"""
    fields
        game_id,
        popularity_type,
        value;

    where game_id = ({game_ids})
        & popularity_type = (
            {POPULARITY_VISITS},
            {POPULARITY_WANT_TO_PLAY}
        );

    limit 500;
    """

    response = requests.post(
        (
            "https://api.igdb.com/v4/"
            "popularity_primitives"
        ),
        headers=get_igdb_headers(
            token
        ),
        data=query,
        timeout=30,
    )

    if not response.ok:
        print(
            "IGDB popularity error: "
            f"{response.status_code}"
        )

        print(
            response.text
        )

    response.raise_for_status()

    popularity_data = (
        response.json()
    )

    print(
        "Popularity records received: "
        f"{len(popularity_data)}"
    )

    games_by_id = {
        game["id"]: game
        for game in games
    }

    for item in popularity_data:
        game_id = item.get(
            "game_id"
        )

        popularity_type = (
            item.get(
                "popularity_type"
            )
        )

        value = float(
            item.get(
                "value",
                0,
            )
            or 0
        )

        if (
            game_id
            not in games_by_id
        ):
            continue

        game = games_by_id[
            game_id
        ]

        if (
            popularity_type
            == POPULARITY_VISITS
        ):
            game[
                "visits"
            ] = value

        elif (
            popularity_type
            == POPULARITY_WANT_TO_PLAY
        ):
            game[
                "want_to_play"
            ] = value

    for game in games:
        game[
            "popularity_score"
        ] = (
            game["visits"]
            * VISITS_WEIGHT
            + game[
                "want_to_play"
            ]
            * WANT_TO_PLAY_WEIGHT
        )

    return games


def mark_featured_games(
    games,
):
    if not games:
        return games

    if DEBUG:
        print(
            "PopScore data:"
        )

        for game in sorted(
            games,
            key=lambda game:
                game[
                    "popularity_score"
                ],
            reverse=True,
        ):
            display_score = (
                game[
                    "popularity_score"
                ]
                * LOG_SCORE_MULTIPLIER
            )

            print(
                f"- {game['name']} | "
                f"Score: "
                f"{display_score:.2f}"
            )

    best_score = max(
        game[
            "popularity_score"
        ]
        for game in games
    )

    relative_min = (
        best_score
        * FEATURED_RELATIVE_THRESHOLD
    )

    featured_threshold = max(
        FEATURED_SCORE_MIN,
        relative_min,
    )

    print(
        "Featured threshold: "
        f"{featured_threshold * LOG_SCORE_MULTIPLIER:.2f}"
    )

    candidates = [
        game
        for game in games
        if (
            game[
                "popularity_score"
            ]
            >= featured_threshold
        )
    ]

    candidates.sort(
        key=lambda game:
            game[
                "popularity_score"
            ],
        reverse=True,
    )

    for game in candidates[
        :MAX_FEATURED_GAMES
    ]:
        game[
            "featured"
        ] = True

    print(
        "Featured games: "
        f"{sum(game['featured'] for game in games)}"
    )

    return sorted(
        games,
        key=lambda game: (
            not game[
                "featured"
            ],
            (
                -game[
                    "popularity_score"
                ]
                if game[
                    "featured"
                ]
                else 0
            ),
            game[
                "name"
            ].lower(),
        ),
    )


def get_platform_labels(
    platform_ids,
):
    platforms = []

    for platform_id in (
        PLATFORM_ORDER
    ):
        if (
            platform_id
            not in platform_ids
        ):
            continue

        label = (
            PLATFORM_LABELS[
                platform_id
            ]
        )

        if label not in platforms:
            platforms.append(
                label
            )

    return platforms


def build_messages(
    games,
):
    today = datetime.now(
        MADRID_TZ
    ).strftime(
        "%d-%m-%Y"
    )

    header = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "         🚀 <b>NEW GAMES OUT TODAY</b>\n"
        f"                         {today}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not games:
        return [
            (
                header
                + "No releases found today."
            )
        ]

    messages = []
    current_message = (
        header
    )

    for game in games:
        game_name = escape(
            game["name"]
        )

        platforms = (
            get_platform_labels(
                game[
                    "platforms"
                ]
            )
        )

        star = (
            "⭐ "
            if game[
                "featured"
            ]
            else ""
        )

        game_block = (
            f"{star}<b>{game_name}</b>\n"
            f"   {' | '.join(platforms)}\n\n"
        )

        if (
            len(current_message)
            + len(game_block)
            > MAX_TELEGRAM_LENGTH
        ):
            messages.append(
                current_message.rstrip()
            )

            current_message = (
                header
                + game_block
            )

        else:
            current_message += (
                game_block
            )

    if current_message.strip():
        messages.append(
            current_message.rstrip()
        )

    return messages


def send_notification(
    text,
):
    # Envía mediante el servicio centralizado
    return notifications.huginn(
        text,
        parse_mode="HTML",
    )


def main():
    # 1. Autenticación con IGDB
    token = get_access_token()

    # 2. Obtener lanzamientos
    games = (
        get_releases_today(
            token
        )
    )

    # 3. Obtener popularidad
    games = (
        add_popularity_data(
            token,
            games,
        )
    )

    # 4. Marcar destacados
    games = (
        mark_featured_games(
            games
        )
    )

    # 5. Construir mensajes
    messages = (
        build_messages(
            games
        )
    )

    # 6. Enviar mediante Huginn
    for message in messages:
        send_notification(
            message
        )


if __name__ == "__main__":  # pragma: no cover
    main()
