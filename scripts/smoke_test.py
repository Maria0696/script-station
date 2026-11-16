# Prueba de producción tras cada despliegue de Vercel (smoke-test.yml).
# Un webhook que responde sin secreto cuenta como fallo, igual que uno caído.

import logging
import os
import time

import requests

from core.logs import configure_logging

logger = logging.getLogger(__name__)

# Dominio de producción; las URLs de cada despliegue tienen SSO de Vercel
BASE_URL = os.getenv("SMOKE_TEST_URL", "https://script-station.vercel.app")

# (método, ruta, estado esperado). Sin secretos: comprueba que la API
# responde y que rechaza a quien no es Telegram ni el cron de Vercel
CHECKS = (
    ("GET", "/api/telegram", 200),
    ("GET", "/api/heimdall", 200),
    ("POST", "/api/telegram", 401),
    ("POST", "/api/heimdall", 401),
    ("GET", "/api/cron", 401),
)

# El dominio puede tardar unos segundos en apuntar al nuevo despliegue
ATTEMPTS = 3
RETRY_DELAY_SECONDS = 15


def run_checks(base_url):
    failures = []

    for method, path, expected in CHECKS:
        try:
            response = requests.request(
                method, f"{base_url}{path}", json={}, timeout=15
            )
            status = response.status_code

        except requests.RequestException as error:
            status = type(error).__name__

        if status != expected:
            failures.append(f"{method} {path}: expected {expected}, got {status}")

    return failures


def smoke_test(base_url=BASE_URL):
    for attempt in range(1, ATTEMPTS + 1):
        failures = run_checks(base_url)

        if not failures:
            logger.info("Smoke test passed: %s", base_url)

            return []

        logger.warning(
            "Smoke test attempt %d/%d failed: %s",
            attempt,
            ATTEMPTS,
            "; ".join(failures),
        )

        if attempt < ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)

    return failures


def main():
    configure_logging()

    failures = smoke_test()

    # El workflow falla y Heimdall avisa
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
