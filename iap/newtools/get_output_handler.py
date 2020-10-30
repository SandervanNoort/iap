import logging
from .LogFormatter import LogFormatter


def get_output_handler(level="INFO"):
    """Print info message, and higher level message including debug level"""
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))
    formatter = LogFormatter(
        "%(levelname)s: %(message)s")
#         {logging.INFO: "%(message)s"})
    handler.setFormatter(formatter)
    return handler
