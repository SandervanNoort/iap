import csv
import six
from .ureader import ureader

if six.PY2:
    class UniDictReader(csv.DictReader):
        """csv.DictReader with six.text_type support"""
        # (too few public) pylint: disable=R0903

        def __init__(self, fobj, fieldnames=None, restkey=None, restval=None,
                     dialect="excel", *args, **kwargs):
            # (too many arguments) pylint: disable=R0913
            csv.DictReader.__init__(self, fobj, fieldnames, restkey, restval,
                                    dialect, *args, **kwargs)
            self.reader = ureader(fobj, dialect, *args, **kwargs)
else:
    UniDictReader = csv.DictReader
