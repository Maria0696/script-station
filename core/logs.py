import logging
import os


def configure_logging():
    # Formato común para los scripts de GitHub Actions.
    # DEBUG=true muestra también los mensajes de depuración
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
