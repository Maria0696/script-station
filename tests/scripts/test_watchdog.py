from datetime import UTC, date, datetime

import pytest

from scripts import watchdog

TODAY = date(2026, 11, 17)


def run(workflow_file, created_at):
    return {"path": f".github/workflows/{workflow_file}", "created_at": created_at}


def test_get_today_uses_utc():
    assert watchdog.get_today() == datetime.now(UTC).date()


@pytest.mark.parametrize(
    ("runs", "missing"),
    [
        # Los dos se lanzaron hoy
        (
            [
                run("videogames.yml", "2026-11-17T07:03:00Z"),
                run("watchlist.yml", "2026-11-17T07:03:05Z"),
            ],
            [],
        ),
        # Solo hay ejecuciones de ayer
        (
            [
                run("videogames.yml", "2026-11-16T07:03:00Z"),
                run("watchlist.yml", "2026-11-16T07:03:05Z"),
            ],
            ["videogames.yml", "watchlist.yml"],
        ),
        # Falta uno; otros workflows no cuentan
        (
            [
                run("videogames.yml", "2026-11-17T07:03:00Z"),
                run("quality-checks.yml", "2026-11-17T08:00:00Z"),
            ],
            ["watchlist.yml"],
        ),
        ([], ["videogames.yml", "watchlist.yml"]),
        ([{"name": "Sin datos"}], ["videogames.yml", "watchlist.yml"]),
    ],
)
def test_find_missing_workflows(runs, missing):
    assert watchdog.find_missing_workflows(runs, TODAY) == missing


def test_build_missing_message():
    message = watchdog.build_missing_message(["watchlist.yml"])

    assert message.startswith("⏰ WORKFLOWS SIN EJECUTAR HOY\n\n👀 Watchlist Monitor\n")
    assert "/api/cron" in message


def test_build_launch_keyboard():
    assert watchdog.build_launch_keyboard(["videogames.yml"]) == {
        "inline_keyboard": [
            [
                {
                    "text": "▶️ Lanzar 🎮 Daily Releases",
                    "callback_data": "dispatch:videogames.yml",
                }
            ]
        ]
    }


def mock_runs(monkeypatch, runs):
    emitted = []

    monkeypatch.setattr(watchdog, "get_workflow_runs", lambda: runs)
    monkeypatch.setattr(watchdog, "get_today", lambda: TODAY)
    monkeypatch.setattr(
        watchdog.notifications,
        "emit",
        lambda event, text, reply_markup: emitted.append((event, text, reply_markup)),
    )

    return emitted


def test_check_daily_workflows_alerts_missing(monkeypatch):
    emitted = mock_runs(monkeypatch, [run("videogames.yml", "2026-11-17T07:03:00Z")])

    assert watchdog.check_daily_workflows() == ["watchlist.yml"]

    event, text, keyboard = emitted[0]

    assert event == "workflow.missed"
    assert "👀 Watchlist Monitor" in text
    assert keyboard["inline_keyboard"][0][0]["callback_data"] == (
        "dispatch:watchlist.yml"
    )


def test_check_daily_workflows_quiet_when_all_ran(monkeypatch, caplog):
    caplog.set_level("INFO", logger=watchdog.__name__)

    emitted = mock_runs(
        monkeypatch,
        [
            run("videogames.yml", "2026-11-17T07:03:00Z"),
            run("watchlist.yml", "2026-11-17T07:03:05Z"),
        ],
    )

    assert watchdog.check_daily_workflows() == []
    assert emitted == []
    assert "All daily workflows ran today." in caplog.text


def test_main(monkeypatch):
    called = []

    monkeypatch.setattr(watchdog, "check_daily_workflows", lambda: called.append(True))

    watchdog.main()

    assert called == [True]
