import six
import chardet


def to_unicode(output):
    """Autodetect unicode"""
    if isinstance(output, six.text_type):
        # already unicode
        return output
    elif output is None or len(output) == 0:
        return ""
    elif isinstance(output, (six.string_types, six.binary_type)):
        detect = chardet.detect(output)
        return output.decode(detect["encoding"])
    else:
        return "{0}".format(output)
