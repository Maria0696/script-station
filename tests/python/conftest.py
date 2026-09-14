import os


TEST_ENV = {
    "TELEGRAM_BOT_TOKEN": "test-huginn-token",
    "TELEGRAM_CHAT_ID": "123456",
    "TELEGRAM_HEIMDALL_BOT_TOKEN": "test-heimdall-token",
    "TELEGRAM_HEIMDALL_CHAT_ID": "654321",
    "IGDB_CLIENT_ID": "test-client-id",
    "IGDB_CLIENT_SECRET": "test-client-secret",
    "GITHUB_TOKEN": "test-github-token",
}


for key, value in TEST_ENV.items():
    os.environ.setdefault(
        key,
        value,
    )