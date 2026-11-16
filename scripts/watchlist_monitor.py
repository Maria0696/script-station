from datetime import date

from core import github, igdb
from core.notifications import (
    notifications,
)


def load_watchlist():
    # Lee la watchlist y su sha desde GitHub
    return github.get_watchlist()


def save_watchlist(
    watchlist,
    sha,
):
    # Guarda la watchlist en GitHub con un commit
    github.save_watchlist(
        watchlist,
        sha,
        message=(
            "chore: update watchlist "
            "release dates"
        ),
    )


def send_notification(
    text,
):
    # Publica un cambio de lanzamiento
    return notifications.emit(
        "game.release_changed",
        text,
    )


def build_change_message(
    game_name,
    platform_label,
    old_date,
    new_date,
):
    # Se anuncia una fecha nueva
    if (
        old_date is None
        and new_date is not None
    ):
        return (
            "📅 NUEVA FECHA DE LANZAMIENTO\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n"
            f"📅 {igdb.display_release_date(new_date)}"
        )

    # Se retira una fecha existente
    if (
        old_date is not None
        and new_date is None
    ):
        return (
            "⚠️ FECHA DE LANZAMIENTO RETIRADA\n\n"
            f"🎮 {game_name}\n"
            f"{platform_label}\n\n"
            f"Antes: {igdb.display_release_date(old_date)}\n"
            "Ahora: Por confirmar"
        )

    old_datetime = (
        date.fromisoformat(
            old_date
        )
    )

    new_datetime = (
        date.fromisoformat(
            new_date
        )
    )

    # Nueva fecha posterior
    if (
        new_datetime
        > old_datetime
    ):
        title = (
            "⏳ RETRASO DE LANZAMIENTO"
        )

    # Nueva fecha anterior
    elif (
        new_datetime
        < old_datetime
    ):
        title = (
            "⏩ ADELANTO DE LANZAMIENTO"
        )

    else:
        return None

    return (
        f"{title}\n\n"
        f"🎮 {game_name}\n"
        f"{platform_label}\n\n"
        f"Antes: {igdb.display_release_date(old_date)}\n"
        f"Ahora: {igdb.display_release_date(new_date)}"
    )


def monitor_watchlist():
    # Carga los juegos que seguimos
    watchlist, sha = (
        load_watchlist()
    )

    if not watchlist:
        print(
            "Watchlist is empty."
        )

        return False

    game_ids = [
        game["id"]
        for game in watchlist
    ]

    # Datos actuales de IGDB
    igdb_games = (
        igdb.get_igdb_games(
            game_ids
        )
    )

    release_dates = (
        igdb.get_release_dates(
            game_ids
        )
    )

    changes_found = False
    pending_messages = []

    for item in watchlist:
        game_id = item[
            "id"
        ]

        igdb_game = (
            igdb_games.get(
                game_id
            )
        )

        if not igdb_game:
            print(
                "Game not found: "
                f"{item['name']} "
                f"({game_id})"
            )

            continue

        # Actualiza nombre y fecha general
        item["name"] = (
            igdb_game.get(
                "name",
                item["name"],
            )
        )

        item[
            "release_date"
        ] = igdb.format_release_date(
            igdb_game.get(
                "first_release_date"
            )
        )

        current_platforms = (
            igdb.build_platform_data(
                igdb_game,
                release_dates.get(
                    game_id,
                    {},
                ),
            )
        )

        stored_platforms = (
            item.get(
                "platforms",
                [],
            )
        )

        # Migra silenciosamente el formato antiguo
        if (
            not stored_platforms
            or not isinstance(
                stored_platforms[0],
                dict,
            )
        ):
            item[
                "platforms"
            ] = current_platforms

            changes_found = True

            print(
                "Migrated platforms: "
                f"{item['name']}"
            )

            continue

        old_by_id = {
            platform["id"]:
                platform
            for platform
            in stored_platforms
        }

        current_by_id = {
            platform["id"]:
                platform
            for platform
            in current_platforms
        }

        # Comprueba cambios de fecha por plataforma
        for platform_id in (
            old_by_id.keys()
            & current_by_id.keys()
        ):
            old_platform = (
                old_by_id[
                    platform_id
                ]
            )

            new_platform = (
                current_by_id[
                    platform_id
                ]
            )

            old_date = (
                old_platform.get(
                    "release_date"
                )
            )

            new_date = (
                new_platform.get(
                    "release_date"
                )
            )

            if (
                old_date
                == new_date
            ):
                continue

            message = (
                build_change_message(
                    item["name"],
                    new_platform[
                        "label"
                    ],
                    old_date,
                    new_date,
                )
            )

            if message:
                pending_messages.append(
                    message
                )

            print(
                "Date changed: "
                f"{item['name']} | "
                f"{new_platform['label']} | "
                f"{old_date} -> "
                f"{new_date}"
            )

            changes_found = True

        # Actualiza siempre el listado de plataformas
        if (
            stored_platforms
            != current_platforms
        ):
            item[
                "platforms"
            ] = current_platforms

            changes_found = True

    # Solo guarda el JSON si hubo cambios
    if changes_found:
        save_watchlist(
            watchlist,
            sha,
        )

    # Avisa solo cuando el cambio ya está guardado:
    # si el guardado falla, el aviso no se repite cada día
    for message in pending_messages:
        send_notification(
            message
        )

    return changes_found


def main():
    # Comprueba cambios en toda la watchlist
    monitor_watchlist()


if __name__ == "__main__":  # pragma: no cover
    main()
