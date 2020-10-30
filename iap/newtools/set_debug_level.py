import logging
import sys


def set_debug_level(value):
    """Set the debug level"""
    upper = value.upper()
    if upper in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        logging.basicConfig(level=getattr(logging, upper))
    else:
        sys.exit("No valid debug option: {0}".format(value))
