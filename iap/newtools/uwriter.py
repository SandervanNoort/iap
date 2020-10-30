import six
import csv

if six.PY2:
    class uwriter(object):  # pylint: disable=C0103
        """csv.reader with six.text_type support"""

        def __init__(self, fobj, *args, **kwargs):
            if isinstance(kwargs.get("delimiter"), six.text_type):
                kwargs["delimiter"] = str(kwargs["delimiter"])
            self.writer = csv.writer(fobj, *args, **kwargs)
            # return csv.writer(fobj, *args, **kwargs)

        def writerow(self, row):
            """Write one row"""
            # self.writer.writerow(row)
            self.writer.writerow([
                item.encode("utf8") if isinstance(item, six.text_type) else
                item
                for item in row])

        def writerows(self, rows):
            """Write multiple rows"""
            for row in rows:
                self.writerow(row)
else:
    uwriter = csv.writer
