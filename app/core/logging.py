"""Configuracao minima de logging.

Chamado uma unica vez em `create_app()`. Em producao o formato vira JSON-ish de
uma linha para facilitar ingestao por agregadores.
"""

import logging
import sys

from app.core.config import settings

_CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_PROD_FORMAT = (
    '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(_PROD_FORMAT if settings.is_production else _CONSOLE_FORMAT)
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO if settings.is_production else logging.DEBUG)

    # SQLAlchemy e barulhento em DEBUG; so sobe quando database_echo estiver ligado.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
