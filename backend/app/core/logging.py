"""Configuración de logging estructurado para el backend."""

import logging
import sys
from logging.config import dictConfig

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    level = "DEBUG" if not settings.is_production else "INFO"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                    "level": level,
                },
            },
            "root": {"handlers": ["stdout"], "level": level},
            "loggers": {
                "uvicorn.error": {"level": level, "propagate": True},
                "uvicorn.access": {"level": "WARNING", "propagate": True},
                "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
            },
        }
    )

    logging.getLogger(__name__).debug("Logging configurado (env=%s)", settings.ENVIRONMENT)
