import os
from .create_dir import create_dir


def touch(fname):
    """Create an empty file"""
    create_dir(fname)
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "w").close()
