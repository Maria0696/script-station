import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Límites de uso y errores temporales del servidor
RETRY_STATUSES = (429, 500, 502, 503, 504)


def create_session(methods, statuses=RETRY_STATUSES):
    # Sesión HTTP que reintenta hasta 3 veces las respuestas temporales.
    # Esperas: inmediata, 1 s y 2 s, o lo que indique Retry-After.
    # Solo se repiten los métodos de "methods", que deben ser seguros
    # de repetir; los errores de conexión se reintentan siempre porque
    # la petición no llegó al servidor
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=statuses,
        allowed_methods=frozenset(methods),
        respect_retry_after_header=True,
        # Devuelve la última respuesta para incluirla en el error
        raise_on_status=False,
    )

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))

    return session


def raise_for_status(response, service, action):
    # Sustituye a response.raise_for_status(), cuyo mensaje incluye la URL:
    # la de Telegram lleva el token del bot, la del token de Twitch el
    # client_secret, y los logs de Actions de este repo son públicos
    if response.ok:
        return

    raise requests.HTTPError(
        f"{service} {action} failed: HTTP {response.status_code}: "
        f"{response.text[:500]}",
        response=response,
    )
