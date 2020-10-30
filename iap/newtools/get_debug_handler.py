import logging


def get_debug_handler(fname, flags="w+"):
    """Get a file handler which logs everything"""
    # create debug file handler and set level to debug
    handler = logging.FileHandler(fname, flags)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(levelname)s - %(asctime)s\n" +
        "%(name)s - %(pathname)s +%(lineno)s\n" +
        "%(message)s\n")
    handler.setFormatter(formatter)
    return handler
