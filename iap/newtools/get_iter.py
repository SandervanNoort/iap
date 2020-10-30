import collections
import six


def get_iter(elem, make_list=False):
    """Return iterable"""
    if isinstance(elem, six.string_types):
        return [elem]
    elif isinstance(elem, collections.Iterable):
        if make_list:
            return list(elem)
        else:
            return elem
    else:
        return [elem]
