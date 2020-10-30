import six
import csv
from .uwriter import uwriter

if six.PY2:
    class UniDictWriter(csv.DictWriter):
        """csv.DictWriter with six.text_type support"""

        def __init__(self, fobj, fieldnames, restval="", extrasaction="raise",
                     dialect="excel", *args, **kwargs):
            # (too many arguments) pylint: disable=R0913
            csv.DictWriter.__init__(self, fobj, fieldnames, restval,
                                    extrasaction, dialect, *args, **kwargs)
            self.writer = uwriter(fobj, dialect, *args, **kwargs)
else:
    UniDictWriter = csv.DictWriter
