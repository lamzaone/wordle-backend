import logging
from logging.config import dictConfig

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    level = "DEBUG" if settings.debug else "INFO"
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                "uvicorn.access": {"level": "INFO", "propagate": False, "handlers": ["console"]},
            },
        }
    )
    logging.getLogger(__name__).debug("Logging configured")
