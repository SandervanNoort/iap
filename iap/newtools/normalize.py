import re
import unicodedata
import six


def normalize(name):
    """Remove non-ascii strings"""

    # the input should by unicode
    if not isinstance(name, six.text_type):
        name = name.decode("utf8")

    # a unicode compatible with ascii
    output = unicodedata.normalize('NFKD', name)
    output = output.encode('ASCII', 'ignore').decode("ASCII")

    # only keep letters, numbers and " ", -, _
    output = "".join([c for c in output
                      if (ord(c) >= ord("a") and ord(c) <= ord("z")) or
                      (ord(c) >= ord("A") and ord(c) <= ord("Z")) or
                      (ord(c) >= ord("0") and ord(c) <= ord("9")) or
                      c in (" ", "-", "_")])
    output = re.sub("[ /]+", "_", output)
    output = re.sub("_+", "_", output)
    output = re.sub("_-_", "-", output)
    return output
