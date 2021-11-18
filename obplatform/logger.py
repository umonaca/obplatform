import logging

logger = logging.getLogger(__package__)

default_handler = logging.StreamHandler()
default_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s] [obplatform-%(module)s] [%(levelname)s] %(message)s"
    )
)

logger.addHandler(default_handler)

__all__ = ["logger"]
