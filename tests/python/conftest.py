import os


TEST_ENV = {
    "TELEGRAM_BOT_TOKEN":
        "test-huginn-token",
    "TELEGRAM_CHAT_ID":
        "123456",
    "TELEGRAM_HEIMDALL_BOT_TOKEN":
        "test-heimdall-token",
    "TELEGRAM_HEIMDALL_CHAT_ID":
        "654321",
    "IGDB_CLIENT_ID":
        "test-client-id",
    "IGDB_CLIENT_SECRET":
        "test-client-secret",
    "GITHUB_TOKEN":
        "test-github-token",
}


for key, value in TEST_ENV.items():
    os.environ.setdefault(
        key,
        value,
    )


def pytest_report_teststatus(
    report,
    config,
):
    # Muestra estado y duración de cada test
    if report.when != "call":
        return None

    duration = (
        report.duration * 1000
    )

    if report.passed:
        return (
            "passed",
            ".",
            f"PASSED ({duration:.2f}ms)",
        )

    if report.failed:
        return (
            "failed",
            "F",
            f"FAILED ({duration:.2f}ms)",
        )

    if report.skipped:
        return (
            "skipped",
            "s",
            f"SKIPPED ({duration:.2f}ms)",
        )

    return None
