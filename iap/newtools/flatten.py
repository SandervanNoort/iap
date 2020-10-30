import collections
import six


def flatten(list_of_lists):
    """Return a flattened list"""

    for elem in list_of_lists:
        if (isinstance(elem, collections.Iterable) and
                not isinstance(elem, six.string_types)):
            for sub in flatten(elem):
                yield sub
        else:
            yield elem
