import pytest
import requests

from core import http


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = text


def test_create_session_retry_policy():
    retry = http.create_session(methods={"GET"}).get_adapter("https://").max_retries

    assert retry.total == 3
    assert set(retry.allowed_methods) == {"GET"}
    assert set(retry.status_forcelist) == set(http.RETRY_STATUSES)
    assert retry.respect_retry_after_header is True
    assert retry.raise_on_status is False


def test_create_session_custom_statuses():
    session = http.create_session(methods={"POST"}, statuses=(429,))
    retry = session.get_adapter("https://").max_retries

    assert set(retry.status_forcelist) == {429}


def test_raise_for_status_accepts_success():
    assert http.raise_for_status(FakeResponse(200), "Service", "action") is None


def test_raise_for_status_message_without_url():
    # Incluye servicio, acción y respuesta, pero nunca la URL
    response = FakeResponse(503, "x" * 600)

    with pytest.raises(requests.HTTPError) as error:
        http.raise_for_status(response, "Telegram", "sendMessage")

    message = str(error.value)

    assert message.startswith("Telegram sendMessage failed: HTTP 503: ")
    assert len(message) < 600
    assert "http" not in message.lower().replace("http 503", "")
    assert error.value.response is response
