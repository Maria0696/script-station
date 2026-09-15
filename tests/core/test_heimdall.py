from datetime import datetime

import pytest

from core import heimdall

# ============================================================
# ESTILO
# ============================================================

def test_build_title_with_icon():
    result = heimdall.build_title(
        "TEST",
        icon="🛡️",
        indent=2,
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        "  🛡️ TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


def test_build_title_without_icon():
    result = heimdall.build_title(
        "TEST",
        indent=1,
    )

    assert result == (
        "━━━━━━━━━━━━━━━━━━━\n"
        " TEST\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ============================================================
# FECHAS
# ============================================================

def test_format_run_time_without_date():
    assert (
        heimdall.format_run_time(
            None
        )
        == "Hora desconocida"
    )


def test_format_run_time_today(
    monkeypatch,
):
    class FakeDatetime(datetime):

        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return cls(
                2026,
                9,
                14,
                15,
                0,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        heimdall,
        "datetime",
        FakeDatetime,
    )

    result = (
        heimdall.format_run_time(
            "2026-09-14T10:30:00Z"
        )
    )

    assert result == (
        "Hoy 12:30"
    )


def test_format_run_time_previous_day(
    monkeypatch,
):
    class FakeDatetime(datetime):

        @classmethod
        def now(
            cls,
            tz=None,
        ):
            return cls(
                2026,
                9,
                14,
                15,
                0,
                tzinfo=tz,
            )

    monkeypatch.setattr(
        heimdall,
        "datetime",
        FakeDatetime,
    )

    result = (
        heimdall.format_run_time(
            "2026-09-13T10:30:00Z"
        )
    )

    assert result == (
        "13-09-2026 12:30"
    )


# ============================================================
# ESTADOS
# ============================================================

@pytest.mark.parametrize(
    (
        "run",
        "expected",
    ),
    [
        (
            None,
            "⚪ Sin datos",
        ),
        (
            {
                "status":
                    "in_progress",
            },
            "🟡 RUNNING",
        ),
        (
            {
                "status":
                    "completed",
                "conclusion":
                    "success",
            },
            "🟢 OK",
        ),
        (
            {
                "status":
                    "completed",
                "conclusion":
                    "cancelled",
            },
            "🟠 CANCELLED",
        ),
        (
            {
                "status":
                    "completed",
                "conclusion":
                    "skipped",
            },
            "⚪ SKIPPED",
        ),
        (
            {
                "status":
                    "completed",
                "conclusion":
                    "neutral",
            },
            "⚪ NEUTRAL",
        ),
        (
            {
                "status":
                    "completed",
                "conclusion":
                    "failure",
            },
            "🔴 FAILED",
        ),
    ],
)
def test_workflow_status(
    run,
    expected,
):
    assert (
        heimdall.workflow_status(
            run
        )
        == expected
    )


# ============================================================
# WORKFLOWS
# ============================================================

def test_get_latest_workflows(
    monkeypatch,
):
    runs = [
        {
            "name":
                (
                    "Daily Video "
                    "Game Releases"
                ),
            "id":
                1,
        },
        {
            "name":
                (
                    "Daily Video "
                    "Game Releases"
                ),
            "id":
                2,
        },
        {
            "name":
                "Quality Checks",
            "id":
                3,
        },
    ]

    monkeypatch.setattr(
        heimdall,
        "get_workflow_runs",
        lambda:
            runs,
    )

    result = (
        heimdall
        .get_latest_workflows()
    )

    assert (
        result[
            "Daily Video Game Releases"
        ][
            "id"
        ]
        == 1
    )

    assert (
        result[
            "Quality Checks"
        ][
            "id"
        ]
        == 3
    )

    assert (
        result[
            "Watchlist Release Monitor"
        ]
        is None
    )


def test_count_incidents():
    latest_runs = {
        "success": {
            "status":
                "completed",
            "conclusion":
                "success",
        },
        "failure": {
            "status":
                "completed",
            "conclusion":
                "failure",
        },
        "timeout": {
            "status":
                "completed",
            "conclusion":
                "timed_out",
        },
        "running": {
            "status":
                "in_progress",
            "conclusion":
                None,
        },
        "missing":
            None,
    }

    result = (
        heimdall
        .count_incidents(
            latest_runs
        )
    )

    assert result == 2


def test_count_all_failure_conclusions():
    latest_runs = {
        conclusion: {
            "status":
                "completed",
            "conclusion":
                conclusion,
        }
        for conclusion
        in heimdall.FAILURE_CONCLUSIONS
    }

    result = (
        heimdall
        .count_incidents(
            latest_runs
        )
    )

    assert result == len(
        heimdall
        .FAILURE_CONCLUSIONS
    )


def test_get_failed_workflows(
    monkeypatch,
):
    latest_runs = {
        "Daily Video Game Releases": {
            "status":
                "completed",
            "conclusion":
                "success",
        },
        "Watchlist Release Monitor": {
            "status":
                "completed",
            "conclusion":
                "failure",
        },
        "Quality Checks":
            None,
    }

    monkeypatch.setattr(
        heimdall,
        "get_latest_workflows",
        lambda:
            latest_runs,
    )

    result = (
        heimdall
        .get_failed_workflows()
    )

    assert list(
        result
    ) == [
        "Watchlist Release Monitor",
    ]


# ============================================================
# STATUS
# ============================================================

def test_build_heimdall_status(
    monkeypatch,
):
    latest_runs = {
        "Daily Video Game Releases": {
            "status":
                "completed",
            "conclusion":
                "success",
            "updated_at":
                "2026-09-14T10:00:00Z",
        },
        "Watchlist Release Monitor": {
            "status":
                "completed",
            "conclusion":
                "failure",
            "updated_at":
                "2026-09-14T11:00:00Z",
        },
        "Quality Checks":
            None,
    }

    monkeypatch.setattr(
        heimdall,
        "get_latest_workflows",
        lambda:
            latest_runs,
    )

    monkeypatch.setattr(
        heimdall,
        "format_run_time",
        lambda date:
            "Hoy 12:00",
    )

    result = (
        heimdall
        .build_heimdall_status()
    )

    assert (
        "🛡️ ESTADO SCRIPT STATION"
        in result
    )

    assert (
        "🎮 Daily Releases — 🟢 OK"
        in result
    )

    assert (
        "👀 Watchlist Monitor — 🔴 FAILED"
        in result
    )

    assert (
        "🧪 Quality Checks — ⚪ Sin datos"
        in result
    )

    assert (
        "⚠️ Incidencias activas: 1"
        in result
    )

    assert (
        result.count(
            "Hoy 12:00"
        )
        == 2
    )


# ============================================================
# FALLOS
# ============================================================

def test_build_heimdall_failures(
    monkeypatch,
):
    failed = {
        "Quality Checks": {
            "status":
                "completed",
            "conclusion":
                "failure",
            "head_branch":
                "master",
            "updated_at":
                "2026-09-14T16:00:00Z",
            "html_url":
                (
                    "https://github.com/"
                    "test/run"
                ),
        },
    }

    monkeypatch.setattr(
        heimdall,
        "format_run_time",
        lambda date:
            "Hoy 18:00",
    )

    result = (
        heimdall
        .build_heimdall_failures(
            failed
        )
    )

    assert (
        "🛡️ FALLOS ACTIVOS"
        in result
    )

    assert (
        "🔴 🧪 Quality Checks"
        in result
    )

    assert (
        "🌿 master"
        in result
    )

    assert (
        "🕒 Hoy 18:00"
        in result
    )

    assert (
        "https://github.com/test/run"
        in result
    )

    assert (
        "⚠️ Total: 1"
        in result
    )


def test_build_heimdall_failures_uses_getter(
    monkeypatch,
):
    monkeypatch.setattr(
        heimdall,
        "get_failed_workflows",
        lambda: {
            "Quality Checks": {
                "status":
                    "completed",
                "conclusion":
                    "failure",
                "updated_at":
                    None,
            }
        },
    )

    monkeypatch.setattr(
        heimdall,
        "format_run_time",
        lambda date:
            "Hora desconocida",
    )

    result = (
        heimdall
        .build_heimdall_failures()
    )

    assert (
        "Quality Checks"
        in result
    )

    assert (
        "Desconocida"
        in result
    )


def test_build_heimdall_failures_without_url(
    monkeypatch,
):
    monkeypatch.setattr(
        heimdall,
        "format_run_time",
        lambda date:
            "Hoy 18:00",
    )

    result = (
        heimdall
        .build_heimdall_failures(
            {
                "Quality Checks": {
                    "head_branch":
                        "master",
                    "updated_at":
                        "date",
                }
            }
        )
    )

    assert (
        "Quality Checks"
        in result
    )

    assert (
        "🔗"
        not in result
    )


def test_build_heimdall_failures_empty():
    result = (
        heimdall
        .build_heimdall_failures(
            {}
        )
    )

    assert (
        "🛡️ FALLOS ACTIVOS"
        in result
    )

    assert (
        "✅ No hay fallos activos."
        in result
    )


# ============================================================
# AYUDA
# ============================================================

def test_build_heimdall_help():
    result = (
        heimdall
        .build_heimdall_help()
    )

    assert (
        "🛡️ COMANDOS"
        in result
    )

    assert (
        "/status"
        in result
    )

    assert (
        "Estado de Script Station."
        in result
    )

    assert (
        "/failures"
        in result
    )

    assert (
        "Muestra los fallos activos."
        in result
    )

    assert (
        "/help"
        in result
    )

    assert (
        "Muestra esta ayuda."
        in result
    )


# ============================================================
# BOTONES
# ============================================================

def test_build_failures_keyboard():
    result = (
        heimdall
        .build_failures_keyboard(
            {
                "Daily Video Game Releases": {
                    "id":
                        456,
                },
                "Quality Checks": {
                    "id":
                        123,
                },
            }
        )
    )

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text":
                        (
                            "🔄 Re-run "
                            "🎮 Daily Releases"
                        ),
                    "callback_data":
                        "rerun:456",
                }
            ],
            [
                {
                    "text":
                        (
                            "🔄 Re-run "
                            "🧪 Quality Checks"
                        ),
                    "callback_data":
                        "rerun:123",
                }
            ],
        ]
    }


def test_build_failures_keyboard_skips_missing_id():
    result = (
        heimdall
        .build_failures_keyboard(
            {
                "Daily Video Game Releases":
                    {},
                "Quality Checks": {
                    "id":
                        123,
                },
            }
        )
    )

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text":
                        (
                            "🔄 Re-run "
                            "🧪 Quality Checks"
                        ),
                    "callback_data":
                        "rerun:123",
                }
            ]
        ]
    }


def test_build_failures_keyboard_empty():
    result = (
        heimdall
        .build_failures_keyboard(
            {
                "Quality Checks":
                    {},
            }
        )
    )

    assert result is None


# ============================================================
# CALLBACKS
# ============================================================

def test_handle_heimdall_callback_unauthorized(
    monkeypatch,
):
    reruns = []

    monkeypatch.setattr(
        heimdall,
        "rerun_failed_workflow_run",
        lambda run_id:
            reruns.append(
                run_id
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "id":
                    "callback-1",
                "data":
                    "rerun:123",
                "message": {
                    "chat": {
                        "id":
                            "999999",
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert reruns == []


def test_handle_heimdall_callback_rerun_success(
    monkeypatch,
):
    captured = {
        "reruns": [],
        "answers": [],
        "messages": [],
    }

    monkeypatch.setattr(
        heimdall,
        "rerun_failed_workflow_run",
        lambda run_id:
            captured[
                "reruns"
            ].append(
                run_id
            ),
    )

    monkeypatch.setattr(
        heimdall,
        "answer_heimdall_callback",
        lambda callback_id, text=None:
            captured[
                "answers"
            ].append(
                (
                    callback_id,
                    text,
                )
            ),
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args:
            captured[
                "messages"
            ].append(
                args
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "id":
                    "callback-1",
                "data":
                    "rerun:123",
                "message": {
                    "chat": {
                        "id":
                            (
                                heimdall
                                .HEIMDALL_CHAT_ID
                            ),
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert (
        captured[
            "reruns"
        ]
        == [
            123,
        ]
    )

    assert (
        captured[
            "answers"
        ]
        == [
            (
                "callback-1",
                "🔄 Re-run solicitado",
            )
        ]
    )

    assert (
        captured[
            "messages"
        ]
        == [
            (
                heimdall
                .HEIMDALL_CHAT_ID,
                (
                    "🔄 Re-run solicitado.\n\n"
                    "🆔 Run #123"
                ),
            )
        ]
    )


def test_handle_heimdall_callback_without_callback_id(
    monkeypatch,
):
    reruns = []
    answers = []
    messages = []

    monkeypatch.setattr(
        heimdall,
        "rerun_failed_workflow_run",
        lambda run_id:
            reruns.append(
                run_id
            ),
    )

    monkeypatch.setattr(
        heimdall,
        "answer_heimdall_callback",
        lambda *args:
            answers.append(
                args
            ),
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args:
            messages.append(
                args
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "data":
                    "rerun:123",
                "message": {
                    "chat": {
                        "id":
                            (
                                heimdall
                                .HEIMDALL_CHAT_ID
                            ),
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert reruns == [
        123,
    ]

    assert answers == []

    assert (
        len(
            messages
        )
        == 1
    )


def test_handle_heimdall_callback_invalid_run_id(
    monkeypatch,
):
    answers = []
    messages = []

    monkeypatch.setattr(
        heimdall,
        "answer_heimdall_callback",
        lambda callback_id, text=None:
            answers.append(
                (
                    callback_id,
                    text,
                )
            ),
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args:
            messages.append(
                args
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "id":
                    "callback-1",
                "data":
                    "rerun:invalid",
                "message": {
                    "chat": {
                        "id":
                            (
                                heimdall
                                .HEIMDALL_CHAT_ID
                            ),
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert answers == [
        (
            "callback-1",
            (
                "❌ No se pudo iniciar "
                "el Re-run"
            ),
        )
    ]

    assert messages == []


def test_handle_heimdall_callback_invalid_without_id(
    monkeypatch,
):
    answers = []

    monkeypatch.setattr(
        heimdall,
        "answer_heimdall_callback",
        lambda *args:
            answers.append(
                args
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "data":
                    "rerun:invalid",
                "message": {
                    "chat": {
                        "id":
                            (
                                heimdall
                                .HEIMDALL_CHAT_ID
                            ),
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert answers == []


def test_handle_heimdall_callback_other_action(
    monkeypatch,
):
    reruns = []

    monkeypatch.setattr(
        heimdall,
        "rerun_failed_workflow_run",
        lambda run_id:
            reruns.append(
                run_id
            ),
    )

    result = (
        heimdall
        .handle_heimdall_callback(
            {
                "id":
                    "callback-1",
                "data":
                    "unknown:123",
                "message": {
                    "chat": {
                        "id":
                            (
                                heimdall
                                .HEIMDALL_CHAT_ID
                            ),
                    }
                },
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert reruns == []


# ============================================================
# COMANDOS
# ============================================================

def test_handle_heimdall_message_ignores_other_chat(
    monkeypatch,
):
    sent = []

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda *args:
            sent.append(
                args
            ),
    )

    result = (
        heimdall
        .handle_heimdall_message(
            {
                "chat": {
                    "id":
                        "999999",
                },
                "text":
                    "/status",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == []


@pytest.mark.parametrize(
    "command",
    [
        "/start",
        "/status",
    ],
)
def test_handle_heimdall_status_commands(
    monkeypatch,
    command,
):
    sent = []

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_status",
        lambda:
            "STATUS",
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda chat_id, message:
            sent.append(
                (
                    chat_id,
                    message,
                )
            ),
    )

    result = (
        heimdall
        .handle_heimdall_message(
            {
                "chat": {
                    "id":
                        (
                            heimdall
                            .HEIMDALL_CHAT_ID
                        ),
                },
                "text":
                    f"  {command}  ",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            heimdall
            .HEIMDALL_CHAT_ID,
            "STATUS",
        )
    ]


def test_handle_heimdall_failures(
    monkeypatch,
):
    sent = []

    failed_workflows = {
        "Quality Checks": {
            "id": 123,
            "status": "completed",
            "conclusion": "failure",
        },
    }

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        (
                            "🔄 Re-run "
                            "🧪 Quality Checks"
                        ),
                    "callback_data":
                        "rerun:123",
                }
            ]
        ]
    }

    monkeypatch.setattr(
        heimdall,
        "get_failed_workflows",
        lambda:
            failed_workflows,
    )

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_failures",
        lambda workflows:
            "FAILURES",
    )

    monkeypatch.setattr(
        heimdall,
        "build_failures_keyboard",
        lambda workflows:
            keyboard,
    )

    def fake_send(
        chat_id,
        message,
        reply_markup=None,
    ):
        sent.append(
            (
                chat_id,
                message,
                reply_markup,
            )
        )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        fake_send,
    )

    result = (
        heimdall
        .handle_heimdall_message(
            {
                "chat": {
                    "id":
                        (
                            heimdall
                            .HEIMDALL_CHAT_ID
                        ),
                },
                "text":
                    "/failures",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            heimdall
            .HEIMDALL_CHAT_ID,
            "FAILURES",
            keyboard,
        )
    ]

# ============================================================
# HELP
# ============================================================

def test_handle_heimdall_help(
    monkeypatch,
):
    sent = []

    monkeypatch.setattr(
        heimdall,
        "build_heimdall_help",
        lambda:
            "HELP",
    )

    monkeypatch.setattr(
        heimdall,
        "send_heimdall_message",
        lambda chat_id, message:
            sent.append(
                (
                    chat_id,
                    message,
                )
            ),
    )

    result = (
        heimdall
        .handle_heimdall_message(
            {
                "chat": {
                    "id":
                        (
                            heimdall
                            .HEIMDALL_CHAT_ID
                        ),
                },
                "text":
                    "/help",
            }
        )
    )

    assert result == {
        "ok": True,
    }

    assert sent == [
        (
            heimdall
            .HEIMDALL_CHAT_ID,
            "HELP",
        )
    ]


# ============================================================
# UPDATE ROUTER
# ============================================================

def test_handle_heimdall_update_routes_callback(
    monkeypatch,
):
    callback = {
        "id":
            "callback-1",
    }

    captured = []

    monkeypatch.setattr(
        heimdall,
        "handle_heimdall_callback",
        lambda received:
            captured.append(
                received
            )
            or {
                "ok": True,
                "callback": True,
            },
    )

    result = (
        heimdall
        .handle_heimdall_update(
            {
                "callback_query":
                    callback,
            }
        )
    )

    assert captured == [
        callback,
    ]

    assert result == {
        "ok": True,
        "callback": True,
    }


def test_handle_heimdall_update_routes_message(
    monkeypatch,
):
    message = {
        "chat": {
            "id":
                "123",
        },
        "text":
            "/status",
    }

    captured = []

    monkeypatch.setattr(
        heimdall,
        "handle_heimdall_message",
        lambda received:
            captured.append(
                received
            )
            or {
                "ok": True,
                "message": True,
            },
    )

    result = (
        heimdall
        .handle_heimdall_update(
            {
                "message":
                    message,
            }
        )
    )

    assert captured == [
        message,
    ]

    assert result == {
        "ok": True,
        "message": True,
    }


def test_handle_heimdall_update_ignores_invalid_callback_and_message():
    result = (
        heimdall
        .handle_heimdall_update(
            {
                "callback_query":
                    "invalid",
                "message":
                    "invalid",
            }
        )
    )

    assert result == {
        "ok": True,
    }


def test_handle_heimdall_update_empty():
    result = (
        heimdall
        .handle_heimdall_update(
            {}
        )
    )

    assert result == {
        "ok": True,
    }
