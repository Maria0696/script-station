import pytest

from scripts import notify

# ============================================================
# MENSAJE
# ============================================================

def test_build_workflow_failure_message():
    result = (
        notify
        .build_workflow_failure_message(
            "Quality Checks",
            "Maria0696/script-station",
            "https://github.com",
            "123456",
        )
    )

    assert result == (
        "⚠️ WORKFLOW FAILED\n\n"
        "🔧 Quality Checks\n"
        "📦 Maria0696/script-station\n\n"
        "🔗 https://github.com/"
        "Maria0696/script-station/"
        "actions/runs/123456"
    )


# ============================================================
# BOTÓN
# ============================================================

def test_build_rerun_keyboard():
    result = (
        notify
        .build_rerun_keyboard(
            "123456"
        )
    )

    assert result == {
        "inline_keyboard": [
            [
                {
                    "text":
                        "🔄 Re-run",
                    "callback_data":
                        "rerun:123456",
                }
            ]
        ]
    }


# ============================================================
# NOTIFICACIÓN
# ============================================================

def test_notify_workflow_failure(
    monkeypatch,
):
    captured = {}

    monkeypatch.setenv(
        "GITHUB_WORKFLOW",
        "Quality Checks",
    )

    monkeypatch.setenv(
        "GITHUB_REPOSITORY",
        "Maria0696/script-station",
    )

    monkeypatch.setenv(
        "GITHUB_SERVER_URL",
        "https://github.com",
    )

    monkeypatch.setenv(
        "GITHUB_RUN_ID",
        "123456",
    )

    def fake_heimdall(
        text,
        reply_markup=None,
        parse_mode=None,
        chat_id=None,
    ):
        captured[
            "text"
        ] = text

        captured[
            "reply_markup"
        ] = reply_markup

        captured[
            "parse_mode"
        ] = parse_mode

        captured[
            "chat_id"
        ] = chat_id

        return {
            "ok": True,
        }

    monkeypatch.setattr(
        notify.notifications,
        "heimdall",
        fake_heimdall,
    )

    result = (
        notify
        .notify_workflow_failure()
    )

    assert result == {
        "ok": True,
    }

    assert (
        "⚠️ WORKFLOW FAILED"
        in captured["text"]
    )

    assert (
        "🔧 Quality Checks"
        in captured["text"]
    )

    assert (
        "📦 Maria0696/script-station"
        in captured["text"]
    )

    assert (
        "actions/runs/123456"
        in captured["text"]
    )

    assert (
        captured[
            "reply_markup"
        ][
            "inline_keyboard"
        ][0][0][
            "callback_data"
        ]
        == "rerun:123456"
    )

    assert (
        captured[
            "parse_mode"
        ]
        is None
    )

    assert (
        captured[
            "chat_id"
        ]
        is None
    )


# ============================================================
# CLI
# ============================================================

def test_main(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        notify,
        "notify_workflow_failure",
        lambda:
            called.append(
                True
            ),
    )

    notify.main(
        [
            "workflow-failed",
        ]
    )

    assert called == [
        True,
    ]


def test_main_uses_sys_argv(
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        notify.sys,
        "argv",
        [
            "notify",
            "workflow-failed",
        ],
    )

    monkeypatch.setattr(
        notify,
        "notify_workflow_failure",
        lambda:
            called.append(
                True
            ),
    )

    notify.main()

    assert called == [
        True,
    ]


def test_main_rejects_unknown_command():
    with pytest.raises(
        SystemExit,
        match=(
            "python -m scripts.notify "
            "workflow-failed"
        ),
    ):
        notify.main(
            [
                "unknown",
            ]
        )
