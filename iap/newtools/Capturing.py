import sys
from .ListIO import ListIO


class Capturing(list):
    """Captures standard output and error"""

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = ListIO(self, "stdout")
        sys.stderr = ListIO(self, "stderr")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
