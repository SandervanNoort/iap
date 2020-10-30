import six
import collections
import csv

if six.PY2:
    class ureader(collections.Iterator):  # pylint: disable=C0103
        """csv.writer with six.text_type support"""

        def __init__(self, fobj, *args, **kwargs):
            if isinstance(kwargs.get("delimiter"), six.text_type):
                kwargs["delimiter"] = str(kwargs["delimiter"])
            self.reader = csv.reader(fobj, *args, **kwargs)

        def next(self):
            """Next row"""
            row = self.reader.next()
            return [
                (value if isinstance(value, (float, six.text_type, int)) else
                 six.text_type(value, "utf8")) for value in row]

        def __next__(self):
            return self.next()

        @property
        def line_num(self):
            """Return current line number"""
            return self.reader.line_num
else:
    ureader = csv.reader
