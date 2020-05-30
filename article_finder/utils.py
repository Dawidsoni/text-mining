import logging


def get_default_logger():
    logging.basicConfig(format="%(levelname)s (%(asctime)s) - %(message)s", level=logging.INFO)
    return logging.getLogger("DEFAULT_LOGGER")

